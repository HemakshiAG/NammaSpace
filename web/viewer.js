// Namma Space — 3D Gaussian Splatting Spatial Viewer Engine
import * as GaussianSplats3D from 'https://cdn.jsdelivr.net/npm/@mkkellogg/gaussian-splats-3d@0.4.6/build/gaussian-splats-3d.module.js';

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

    this.keyState = { KeyW: false, KeyA: false, KeyS: false, KeyD: false };
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
    const keyMap = { KeyW: 'key-w', KeyA: 'key-a', KeyS: 'key-s', KeyD: 'key-d' };
    const el = document.getElementById(keyMap[code]);
    if (el) {
      el.classList.toggle('key-active', active);
    }
  }

  async load() {
    this.hideError();
    this.showLoading('Connecting to 3D reconstruction stream...');

    try {
      // 1. Fetch initial camera position from cameras.json
      let camPos = undefined;
      let camLookAt = undefined;

      try {
        const response = await fetch(this.camerasPath);
        if (response.ok) {
          const cd = await response.json();
          if (cd && cd.cameras && cd.cameras.length > 0) {
            const initialIdx = cd.initial ?? Math.floor(cd.cameras.length / 2);
            const cam = cd.cameras[initialIdx] || cd.cameras[0];
            const p = cam.pos, fwd = cam.forward;
            camPos = p;
            camLookAt = [p[0] + fwd[0], p[1] + fwd[1], p[2] + fwd[2]];
          }
        }
      } catch (err) {
        console.warn('Could not read cameras.json, falling back to default camera placement.', err);
      }

      // 2. Initialize GaussianSplats3D Viewer
      const viewerOpts = {
        cameraUp: [0, -1, 0],
        selfDrivenMode: true,
        useBuiltInControls: true,
        rootElement: this.container,
        renderMode: GaussianSplats3D.RenderMode.Always,
      };

      if (camPos) viewerOpts.initialCameraPosition = camPos;
      if (camLookAt) viewerOpts.initialCameraLookAt = camLookAt;

      // Clean up prior instance if re-initializing
      if (this.viewer) {
        try { this.viewer.dispose(); } catch (_) {}
        this.container.innerHTML = '';
      }

      this.viewer = new GaussianSplats3D.Viewer(viewerOpts);

      // 3. Load Splat Scene with progress tracking
      const sceneOpts = {
        splatAlphaRemovalThreshold: 5,
        showLoadingUI: false,
        onProgress: (pct) => {
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

      await this.viewer.addSplatScene(this.scenePath, sceneOpts);

      // Scene is ready
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

    const tick = () => {
      if (this.isRunning && this.viewer && this.viewer.camera) {
        const p = this.viewer.camera.position;
        if (p && this.coordsEl) {
          this.coordsEl.textContent = `x:${fmt(p.x)}  y:${fmt(p.y)}  z:${fmt(p.z)}`;
        }
      }
      this.animationFrameId = requestAnimationFrame(tick);
    };

    tick();
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
