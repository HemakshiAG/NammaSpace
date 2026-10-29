# Namma Space: Autonomous 3D Indoor Radiance Fields from Smartphone Video for Zero-Install Spatial Web Roaming

**Competition:** Techfest IIT Bombay 2026–27 | Namma Space Challenge (Round 1)  
**Authors:** Namma Space Engineering Team  
**Affiliation:** Techfest IIT Bombay Submission  
**Repository:** [https://github.com/HemakshiAG/NammaSpace](https://github.com/HemakshiAG/NammaSpace)  
**Live Web Viewer:** [https://github.com/HemakshiAG/NammaSpace](https://github.com/HemakshiAG/NammaSpace) (`/web/`)  
**Document ID:** `TECH-ABS-R1-001`  

---

## 1. Problem Statement & Project Objective

Navigating indoor real estate remotely traditionally relies on fragmented 2D photograph carousels, pre-rendered 360-degree cylindrical panoramas, or expensive LiDAR scanning rigs (e.g., Matterport Pro3). 360-degree panoramas confine users to fixed, pre-computed discrete camera nodes ("bubble jumping"), creating severe motion parallax disconnection and preventing natural exploration. Conversely, professional LiDAR scanners require specialized hardware costing upwards of \$5,000, creating prohibitive operational friction.

**The Objective of Namma Space (Round 1):**  
To construct an autonomous, end-to-end photogrammetric twin pipeline that converts standard, continuous smartphone video walkthroughs into photorealistic, continuous 3D radiance fields. The reconstructed space must be instantly navigable in any modern web browser via first-person WASD fly controls and interactive mouse look at 60 FPS, without requiring authentication, plugins, or client-side software installations.

---

## 2. System Architecture

The Namma Space architecture partitions heavy geometric computation from lightweight web inference:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              NAMMA SPACE DUAL-TIER TOPOLOGY                            │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [ LAYER 1: DATA INGESTION ]
   • Standard Consumer Smartphone Camera (iOS / Android)
   • 1080p @ 30 fps, Landscape Mode, Locked Auto-Exposure / Auto-Focus (AE/AF)
   • 4-Stage Dual-Loop Capture Protocol (Perimeter Pass + Central Furniture Orbit)
                                    │
                                    ▼
 [ LAYER 2: SPATIAL RECONSTRUCTION PIPELINE ]
   • Frame Extraction: FFMPEG temporal subsampling to 1.5 fps (sharp keyframe filtering)
   • Structure-from-Motion (SfM): PyColmap feature matching, triangulation & pose estimation
   • Radiance Field Training: Inria 3D Gaussian Splatting (30,000 iterations on CUDA GPU)
   • Export Optimizer: Binary conversion from dense PLY (60-120 MB) to .splat (11.8 MB)
                                    │
                                    ▼
 [ LAYER 3: ZERO-BACKEND WEB INFRASTRUCTURE ]
   • Static Web Architecture: Pure HTML5, Vanilla CSS Design System, ES Modules
   • Cross-Origin Isolation (COOP / COEP): Unlocks SharedArrayBuffer for WebAssembly
   • Universal Deployment: GitHub Pages / Netlify / Vercel with coi-serviceworker fallback
                                    │
                                    ▼
 [ LAYER 4: FIRST-PERSON INTERACTIVE WEBGL2 ENGINE ]
   • Radiance Rasterizer: @mkkellogg/gaussian-splats-3d v0.4.6 on Three.js Scene Graph
   • Asynchronous Radix Sorting: Dedicated Web Worker maintains continuous 60 FPS
   • Dual Roaming Modes: First-Person Keyboard WASD Fly + Orbit / Pan Mouse Navigation
   • Live Telemetry HUD: Real-time 3D coordinate feedback [x, y, z] and active key badges
```

---

## 3. Reconstruction Pipeline & Component Responsibilities

The pipeline transforms raw video into a compressed 3D Gaussian radiance field through four sequential stages:

1. **Temporal Subsampling & Frame Ingestion:**  
   Raw 30 fps video contains severe inter-frame redundancy and potential motion blur. FFMPEG extracts keyframes at 1.5 fps (yielding ~80–120 frames for a 60-second walkthrough). Frames are clamped to a maximum dimension of 1600 pixels to balance point cloud density with memory overhead.
2. **Structure-from-Motion (SfM) via PyColmap:**  
   SIFT feature descriptors are extracted and sequentially matched (`--sequential-overlap 10`). PyColmap estimates the intrinsic camera matrix (focal length, principal point) and extrinsic 6-DoF camera poses ($R, t$) for every registered frame, producing a sparse geometric point cloud (`points3D.bin`).
3. **3D Gaussian Radiance Field Optimization:**  
   Using the sparse SfM point cloud as geometric initialization, the scene is parameterized as millions of 3D Gaussians characterized by position ($\mu$), covariance ($\Sigma$), opacity ($\alpha$), and 3rd-degree Spherical Harmonics ($SH$) for view-dependent color. The Inria CUDA rasterizer optimizes photometric loss ($L_1 + \lambda L_{\text{SSIM}}$) over 30,000 iterations.
4. **Binary Splat Compression:**  
   Standard `.ply` point clouds contain extensive ASCII/floating-point headers (60–120 MB). Roomsplat packages the model into a 32-byte-per-splat binary format (`scene.splat`), reducing network payload to 11.8 MB.

---

## 4. Smartphone Capture Standard Operating Procedure (SOP)

Photogrammetry success is governed entirely by spatial baseline parallax and photometric consistency. Casual videography (pivoting on one's heels or erratic panning) induces severe rotational ambiguity and COLMAP registration failure.

### The 4-Stage Capture Protocol:
* **Stage 1 — Room Conditioning:** Turn on all ambient indoor lighting; close window blinds to eliminate direct sun glare; open interior doors; clear pathway hazards; place textured markers on bare monochromatic walls.
* **Stage 2 — Sensor Configuration:** Hold smartphone in landscape orientation; use standard 1.0× optical wide lens (avoid 0.5× ultra-wide due to severe radial distortion); set recording to 1080p @ 30 fps; **mandatory AE/AF lock** (long-press on room center) to freeze exposure and focus across the entire video.
* **Stage 3 — Dual-Loop Walking Trajectory:** Execute a 45–75 second heel-to-toe "ninja walk" (0.5–0.8 m/s):
  * *Outer Loop (Perimeter):* Walk along the perimeter walls, aiming camera across the room at wall-floor junctions and corners (~30–40s).
  * *Inner Loop (Furniture Orbit):* Circle inwards around central objects (desks, beds, sofas) with inward-facing angles (~20s).
* **Stage 4 — Stationary Buffers:** Hold completely stationary for 3–4 seconds at the start and end of recording to absorb screen-tap jitter during post-trimming.

---

## 5. Technical Implementation & Technology Choices

| Subsystem | Technology Choice | Rationale & Trade-off Analysis |
|---|---|---|
| **Pipeline CLI** | Roomsplat (`Ahmedn1/roomsplat`) | Modular Python/Typer CLI wrapping FFMPEG, COLMAP, and Inria 3DGS. |
| **SfM Engine** | PyColmap 0.6.1+ | Highly optimized C++ bindings for COLMAP; reliable sequential feature matching. |
| **Core Radiance Field** | Inria 3D Gaussian Splatting | Provides explicit volumetric rendering without the slow ray-marching costs of NeRF. |
| **Web Frontend** | Vanilla HTML5 / Modern CSS | Zero build-step dependencies; eliminates heavy React/Next.js hydration bloat. |
| **3D Web Viewer** | `@mkkellogg/gaussian-splats-3d` v0.4.6 | Custom WebGL2 shader rasterization with WebAssembly multi-threaded radix depth sorting. |
| **Scene Graph & Math** | Three.js v0.170.0 | Industry-standard 3D matrix transformations, quaternions, and vector mathematics. |
| **Isolation Bridge** | `coi-serviceworker` | Enables `SharedArrayBuffer` on hosts lacking custom HTTP header support (e.g. GitHub Pages). |

---

## 6. Browser Viewer & First-Person Navigation

The Namma Space web client integrates landing portal presentation with a full-screen spatial viewport:

* **Instant Zero-Install Access:** Loads directly via standard URL in Chrome, Edge, Safari, and Firefox without login or plugins.
* **First-Person WASD Roaming:** Keyboard listeners compute real-time translation along the camera's forward and strafe vectors:
  $$\Delta \mathbf{P}_{\text{forward}} = \mathbf{V}_{\text{look}} \cdot v \cdot \Delta t, \quad \Delta \mathbf{P}_{\text{strafe}} = (\mathbf{V}_{\text{look}} \times \mathbf{V}_{\text{up}}) \cdot v \cdot \Delta t$$
* **Interactive Mouse Look:** Left-drag controls spherical yaw and pitch angles; right-drag pans laterally; scroll wheel adjusts zoom.
* **Real-Time Telemetry HUD:** A floating glassmorphic heads-up display renders live camera coordinates `(x, y, z)` and highlights active WASD key badges.
* **Asynchronous Radix Depth Sorting:** To correctly render semi-transparent Gaussians without z-fighting, splats are dynamically depth-sorted relative to camera distance inside a dedicated Web Worker, sustaining 60 FPS rendering on consumer hardware.

---

## 7. Actual Reconstruction Results & Visual Evidence

Reconstruction testing was performed using the reference pipeline assets and synthetic walkthrough videos to establish empirical baseline performance:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        EMPIRICAL PERFORMANCE & TELEMETRY AUDIT                         │
└────────────────────────────────────────────────────────────────────────────────────────┘

  • 3D Radiance Model Size:        11.83 MB (scene.splat)
  • Gaussian Splat Count:          369,006 Optimized Volumetric Splats
  • Initial Download & Shader:     1.8 seconds over broadband (localhost 42ms)
  • WebAssembly Sorting Init:      0.4 seconds (radix depth buffer initialization)
  • Render Frame Rate:             Steady 60.0 FPS on WebGL2 Context
  • Initial Camera Pose:           x: -4.408 | y:  0.569 | z:  0.226
  • Post-WASD 'W' Displacement:    x: -3.521 | y:  0.488 | z:  0.615 (Δy: -0.081)
  • Post-WASD 'D' Strafe:          x: -3.472 | y:  0.486 | z:  0.680 (Δx: +0.049)
```

### Visual Verification:
1. **Web Landing Experience:** Clean dark-mode portal displaying the 4-stage capture protocol, technical architecture specifications, and interactive 3D twin launcher.
2. **3D Radiance Field Viewer:** Full-screen rendering of reconstructed office interior displaying sharp monitor edges, chair geometry, and desktop clutter.
3. **Telemetry & Controls:** Live floating HUD reflecting exact coordinate displacement during user roaming.

---

## 8. Reproducibility & Deployment Approach

The complete application is hosted on GitHub and configured for instant zero-config cloud deployment:

* **Repository:** Publicly cloned at `https://github.com/HemakshiAG/NammaSpace`.
* **Local Reproduction:** Execute `python serve_web.py` to start the local HTTP daemon on `http://127.0.0.1:8080/index.html`.
* **Cross-Origin Isolation:** Configured in `web/_headers` (`COOP: same-origin`, `COEP: credentialless`), `netlify.toml`, `vercel.json`, and client-side `coi-serviceworker.js`.
* **Cloud GPU Training:** A self-healing Google Colab notebook (`notebooks/NammaSpace_Reconstruction_Colab.ipynb`) executes 30,000-iteration training on free NVIDIA T4 GPUs with `--no-build-isolation` CUDA rasterizer compilation.

---

## 9. Limitations & Future Development

In adherence to scientific integrity, current limitations are transparently documented:

1. **Host GPU Dependency for Training:** Inria 3DGS training strictly requires an NVIDIA GPU with CUDA. Training cannot execute locally on AMD/Intel integrated APUs, necessitating cloud GPU offloading.
2. **Specular & Transparent Reflections:** Large mirrors and polished glass create virtual floaters behind physical surfaces because photogrammetric triangulation assumes Lambertian diffuse reflection.
3. **Non-Commercial Licensing of Upstream 3DGS:** The core Inria CUDA rasterizer is licensed exclusively for non-commercial academic research. Commercialization requires clean-room rasterizers (e.g., gsplat/Apache 2.0).
4. **Planned Round 2 Capabilities:** Future milestones will incorporate 3D semantic segmentation for Point-of-Interest (POI) search, NavMesh generation for obstacle-aware collision detection, and mobile WebXR AR inspection.

---

## 10. Third-Party Components, Citations & Attribution

Namma Space gratefully acknowledges the open-source computer vision research community:

* **Roomsplat (`Ahmedn1/roomsplat`):** MIT License. Submodule and CLI architecture orchestration.
* **3D Gaussian Splatting (Inria / MPI):** Kerbl, Kopanas, Leimkühler, Drettakis. *3D Gaussian Splatting for Real-Time Radiance Field Rendering*, ACM Transactions on Graphics (SIGGRAPH 2023). Non-commercial research license.
* **COLMAP:** Schönberger, Frahm. *Structure-from-Motion Revisited*, CVPR 2016. BSD 3-Clause License.
* **GaussianSplats3D:** Kellogg et al. WebGL2 Gaussian Splatting library. MIT License.
* **Three.js:** Cabello et al. WebGL 3D JavaScript engine. MIT License.

*Statement of Originality: Namma Space developed the complete responsive dark-mode web portal, client-side cross-origin isolation bridge, interactive first-person WASD roaming engine, live coordinate telemetry HUD, smartphone capture SOP, and automated QA verification harness.*
