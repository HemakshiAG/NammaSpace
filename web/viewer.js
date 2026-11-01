// Namma Space — 3D Gaussian Splatting Spatial Viewer Engine
import * as GaussianSplats3D from 'https://cdn.jsdelivr.net/npm/@mkkellogg/gaussian-splats-3d@0.4.6/build/gaussian-splats-3d.module.js';
import * as THREE from 'three';

export class NammaSpaceViewer {
  constructor(options = {}) {
    this.container = options.container || document.getElementById('canvas-container');
    this.loadingOverlay = document.getElementById('viewer-loading');
    this.progressFill = document.getElementById('loading-progress-fill');
    this.statusDetail = document.getElementById('loading-status-detail');
    this.errorOverlay = document.getElementById('viewer-error');
    this.errorDetail = document.getElementById('error-description-text');
    this.coordsEl = document.getElementById('viewer-coords');

    this.viewer = null;
    this.isRunning = false;
    this.animationFrameId = null;
    this.scenePath = options.scenePath || './scene.splat';
    this.camerasPath = options.camerasPath || './cameras.json';

    this.keyState = {
      KeyW: false,
      KeyA: false,
      KeyS: false,
      KeyD: false,
      ArrowUp: false,
      ArrowDown: false,
      ArrowLeft: false,
      ArrowRight: false,
      KeyQ: false,
      KeyE: false,
      ShiftLeft: false,
      ShiftRight: false,
    };
    this.initKeyListeners();
  }

  initKeyListeners() {
    window.addEventListener('keydown', (e) => {
      if (this.keyState.hasOwnProperty(e.code)) {
        this.keyState[e.code] = true;
        this.updateKeyHUD(e.code, true);
      }
    });

    window.addEventListener('keyup', (e) => {
      if (this.keyState.hasOwnProperty(e.code)) {
        this.keyState[e.code] = false;
        this.updateKeyHUD(e.code, false);
      }
    });
  }

  updateKeyHUD(code, active) {
    const keyMap = {
      KeyW: 'key-w',
      ArrowUp: 'key-w',
      KeyA: 'key-a',
      ArrowLeft: 'key-a',
      KeyS: 'key-s',
      ArrowDown: 'key-s',
      KeyD: 'key-d',
      ArrowRight: 'key-d',
    };
    const el = document.getElementById(keyMap[code]);
    if (el) {
      el.classList.toggle('key-active', active);
    }
  }

  async load() {
    this.hideError();
    this.showLoading('Connecting to 3D reconstruction stream...');
    console.log('[NammaViewer] Starting load()...');

    try {
      console.log('[NammaViewer] Step 1: fetching cameras.json...');
      let camPos = undefined;
      let camLookAt = undefined;

      try {
        const response = await fetch(this.camerasPath + '?t=' + Date.now());
        if (response.ok) {
          const cd = await response.json();
          if (cd && cd.cameras && cd.cameras.length > 0) {
            const initialIdx = cd.initial ?? Math.floor(cd.cameras.length / 2);
            const cam = cd.cameras[initialIdx] || cd.cameras[0];
            const p = cam.pos, fwd = cam.forward;
            camPos = p;
            camLookAt = [p[0] + fwd[0], p[1] + fwd[1], p[2] + fwd[2]];
            console.log('[NammaViewer] Camera pose loaded:', { camPos, camLookAt });
          }
        }
      } catch (err) {
        console.warn('Could not read cameras.json, falling back to default camera placement.', err);
      }

      console.log('[NammaViewer] Step 2: Creating GaussianSplats3D.Viewer instance...');
      const viewerOpts = {
        cameraUp: [0, -1, 0],
        selfDrivenMode: true,
        useBuiltInControls: true,
        rootElement: this.container,
        renderMode: GaussianSplats3D.RenderMode.Always,
        antialiased: true,
      };

      if (camPos && camLookAt) {
        viewerOpts.initialCameraPosition = camPos;
        viewerOpts.initialCameraLookAt = camLookAt;
      }

      if (this.viewer) {
        try { this.viewer.dispose(); } catch (_) {}
        this.container.innerHTML = '';
      }

      this.viewer = new GaussianSplats3D.Viewer(viewerOpts);
      console.log('[NammaViewer] Step 3: Viewer instantiated. Adding splat scene:', this.scenePath);

      const sceneOpts = {
        format: GaussianSplats3D.SceneFormat.Splat,
        splatAlphaRemovalThreshold: 5,
        showLoadingUI: false,
        onProgress: (pct) => {
          console.log(`[NammaViewer Progress] ${pct.toFixed(1)}%`);
          if (this.progressFill) this.progressFill.style.width = `${pct}%`;
          if (this.statusDetail) {
            if (pct < 100) {
              this.statusDetail.textContent = `Streaming 32-byte Gaussian records… ${pct.toFixed(0)}%`;
            } else {
              this.statusDetail.textContent = 'Constructing WebAssembly sorting buffers…';
            }
          }
        },
      };

      const splatUrl = this.scenePath.includes('?') ? this.scenePath : `${this.scenePath}?v=${Date.now()}`;
      await this.viewer.addSplatScene(splatUrl, sceneOpts);
      console.log('[NammaViewer] Step 4: addSplatScene complete! Starting viewer...');

      this.viewer.start();
      this.isRunning = true;
      this.hideLoading();
      this.startTelemetryLoop();
      console.log('NammaSpaceViewer: 3D scene loaded and rendering at 60 FPS.');
    } catch (error) {
      console.error('NammaSpaceViewer failed to initialize:', error);
      this.showError(`Failed to load 3D Gaussian Splat scene (${this.scenePath}).\nError: ${error.message || error}`);
    }
  }

  startTelemetryLoop() {
    if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);

    const fmt = (n) => (n !== undefined ? n.toFixed(3).padStart(7) : '  0.000');
    let lastTime = performance.now();

    const forward = new THREE.Vector3();
    const right = new THREE.Vector3();
    const up = new THREE.Vector3();
    const moveDelta = new THREE.Vector3();

    const tick = (now) => {
      const dt = Math.min((now - lastTime) / 1000, 0.1);
      lastTime = now;

      if (this.isRunning && this.viewer && this.viewer.camera) {
        const cam = this.viewer.camera;
        const p = cam.position;

        if (p && this.coordsEl) {
          this.coordsEl.textContent = `x:${fmt(p.x)}  y:${fmt(p.y)}  z:${fmt(p.z)}`;
        }

        // --- 6-DOF First-Person Flight Controller ---
        let baseSpeed = 2.0; // units per second
        if (this.keyState.ShiftLeft || this.keyState.ShiftRight) {
          baseSpeed *= 2.2; // sprint
        }
        const moveDist = baseSpeed * dt;

        cam.getWorldDirection(forward);
        up.copy(cam.up).normalize();
        right.crossVectors(forward, up).normalize();

        moveDelta.set(0, 0, 0);

        if (this.keyState.KeyW || this.keyState.ArrowUp) {
          moveDelta.addScaledVector(forward, moveDist);
        }
        if (this.keyState.KeyS || this.keyState.ArrowDown) {
          moveDelta.addScaledVector(forward, -moveDist);
        }
        if (this.keyState.KeyD || this.keyState.ArrowRight) {
          moveDelta.addScaledVector(right, moveDist);
        }
        if (this.keyState.KeyA || this.keyState.ArrowLeft) {
          moveDelta.addScaledVector(right, -moveDist);
        }
        if (this.keyState.KeyE) {
          moveDelta.addScaledVector(up, moveDist);
        }
        if (this.keyState.KeyQ) {
          moveDelta.addScaledVector(up, -moveDist);
        }

        if (moveDelta.lengthSq() > 0) {
          cam.position.add(moveDelta);
          if (this.viewer.controls && this.viewer.controls.target) {
            this.viewer.controls.target.add(moveDelta);
          }
        }
      }
      this.animationFrameId = requestAnimationFrame(tick);
    };

    this.animationFrameId = requestAnimationFrame(tick);
  }

  showLoading(msg) {
    if (this.loadingOverlay) this.loadingOverlay.style.display = 'flex';
    if (this.statusDetail) this.statusDetail.textContent = msg || 'Loading…';
    if (this.progressFill) this.progressFill.style.width = '0%';
  }

  hideLoading() {
    if (this.loadingOverlay) this.loadingOverlay.style.display = 'none';
  }

  showError(msg) {
    this.hideLoading();
    if (this.errorOverlay) this.errorOverlay.style.display = 'flex';
    if (this.errorDetail) this.errorDetail.textContent = msg;
  }

  hideError() {
    if (this.errorOverlay) this.errorOverlay.style.display = 'none';
  }

  dispose() {
    this.isRunning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.viewer) {
      try { this.viewer.dispose(); } catch (_) {}
      this.viewer = null;
    }
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}
