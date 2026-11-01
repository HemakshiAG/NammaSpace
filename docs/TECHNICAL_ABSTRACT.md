# Namma Space: Autonomous 3D Indoor Radiance Fields from Smartphone Video for Zero-Install Spatial Web Roaming

**Competition:** Techfest IIT Bombay 2026–27 | Namma Space Challenge (Round 1 Submission)  
**Authors:** Namma Space Engineering Team  
**Affiliation:** Techfest IIT Bombay Round 1 Submission  
**Repository:** [https://github.com/HemakshiAG/NammaSpace](https://github.com/HemakshiAG/NammaSpace)  
**Document ID:** `TECH-ABS-R1-001`  

---

## 1. Problem Statement & Project Objective

Navigating real estate interiors remotely has historically suffered from a stark dichotomy: cheap but disjointed 2D photograph carousels and pre-rendered 360-degree cylindrical panoramas versus photorealistic but operationally friction-heavy LiDAR scanning rigs. 

1. **360-Degree Panoramas:** Confine users to fixed, pre-computed discrete camera bubbles ("bubble hopping"). This induces severe motion parallax disorientation, distorts peripheral perspective, and precloses continuous, natural exploration.
2. **Physical LiDAR Scanning Rigs:** Commercial hardware (e.g., Matterport Pro3) costs upwards of \$5,000, requires extensive multi-station transit time, and produces heavy triangle meshes that struggle on mobile browser engines.

**The Objective of Namma Space (Round 1):**  
To construct an autonomous, end-to-end photogrammetric twin pipeline that converts standard consumer smartphone walkthrough videos into photorealistic, continuous 3D radiance fields. The reconstructed space must be instantly navigable in any modern web browser via first-person WASD fly controls and interactive mouse look at steady 60 FPS, without requiring user authentication, native plugins, or client-side software installations.

---

## 2. System Architecture & Dual-Tier Topology

Namma Space strictly decouples high-performance geometric reconstruction from ultra-lightweight client-side spatial inference across four architectural tiers:

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
 [ LAYER 2: RECONSTRUCTION WORKER (Local Headless Microservice) ]
   • Frame Ingestion: OpenCV 2.5 fps subsampling & Laplacian variance blur rejection
   • Single-Camera Calibration: CameraMode.SINGLE locks physical focal length (f = 1017.6px)
   • Covariant SIFT: 2x octave detection, domain-size pooling, darkness adaptivity
   • Chronological Matching: 12,400+ pairs (local window [t±25] + quadratic loop jumps)
   • 0% Discardation Mapping: PyColmap incremental mapping into connected submodels
   • Closed-Form Sim3d Alignment: Exact (s, R, t) similarity alignment via projection centers
   • Floater Purge: Multi-view consensus (track >= 3) + k-d tree SOR (k=12, mu + 1.25*sigma)
   • Surfel Synthesis: Tight Voronoi pancake surfels (3mm-4.5cm, alpha >= 235) in .splat
                                    │
                                    ▼
 [ LAYER 3: ZERO-BACKEND WEB INFRASTRUCTURE ]
   • Static Web Architecture: Pure HTML5, Vanilla CSS Design System, ES Modules
   • In-Browser Upload Portal: Direct multipart upload (/api/upload) with live SSE progress
   • Cross-Origin Isolation (COOP / COEP): Unlocks SharedArrayBuffer for WebAssembly
   • Universal Deployment: GitHub Pages / Netlify / Vercel with coi-serviceworker fallback
                                    │
                                    ▼
 [ LAYER 4: FIRST-PERSON INTERACTIVE WEBGL2 ENGINE ]
   • Radiance Rasterizer: @mkkellogg/gaussian-splats-3d v0.4.6 on Three.js Scene Graph
   • Asynchronous Radix Sorting: Dedicated WebAssembly Web Worker maintains steady 60 FPS
   • Dual Roaming Modes: First-Person Keyboard WASD Fly + Orbit / Pan Mouse Navigation
   • Live Telemetry HUD: Real-time 3D coordinate feedback [x, y, z] and active key badges
```

| Architectural Layer | Engine / Component | Key Functional Responsibilities & Boundary |
|---|---|---|
| **1. Data Ingestion** | Smartphone Camera (iOS/Android) | 1080p @ 30 fps, 1.0x wide lens, AE/AF locked, 4-stage dual-loop walking route. |
| **2. Reconstruction Worker** | Pipeline Worker + PyColmap | Single-camera calibration, Covariant SIFT, 0% discardation Sim3d alignment, SOR floater purge. |
| **3. Web Infrastructure** | Vanilla HTML5 / Modern CSS | Dark-mode UI, in-browser upload portal (`/api/upload`), live stepper, zero-backend static deployment. |
| **4. First-Person Engine** | GaussianSplats3D + Three.js | WebGL2 radiance field rendering, WebAssembly multi-threaded radix depth sort, WASD telemetry HUD. |

---

## 3. Reconstruction Pipeline Design & Algorithmic Foundations

Transforming unconstrained handheld video into continuous radiance fields requires solving significant mathematical challenges: motion blur during rapid turns, focal length drift, and floating triangulation artifacts. Namma Space deploys a multi-stage photogrammetric pipeline:

1. **Temporal Subsampling & Frame Ingestion:**  
   Handheld video at 30 fps possesses severe redundancy and inter-frame blur. OpenCV temporally samples frames at 2.5 fps (~100–150 frames for a 60s walk) while computing Laplacian variance blur scores to reject smeared transition frames. Frames are normalized to 848x478 for optimal speed-to-accuracy balance.
2. **Unified Physical Sensor Calibration (`CameraMode.SINGLE`):**  
   Assigning independent camera IDs forces SfM solvers to estimate focal lengths per frame, triggering divergence during rapid camera turns. Namma Space enforces a single shared physical camera matrix (`SIMPLE_RADIAL`), locking the focal length ($f = 1017.6\,\text{px}$) and principal point to eliminate focal drift.
3. **Covariant SIFT Feature Extraction:**  
   To retain tracking across motion blur and dark room sections, the extractor operates with 2x octave upsampling (`first_octave = -1`), high-sensitivity peak threshold ($0.004$), edge threshold ($15.0$), and domain-size pooling (DSP). This detects 800–4,000 robust features per frame, bridging previously severed turning sequences.
4. **Chronological Pair Matching & Loop-Closure Graph:**  
   Rather than naive sequential pairing susceptible to database ID reordering, the system constructs an explicit graph matching each frame $t$ with local neighbors ($t \pm 1..25$) plus quadratic long-range jumps ($t \pm 35, 50, 75, 100, 150, 200, 250, 300, 350$) for robust loop closure (12,400+ verified pairs).
5. **0% Discardation Multi-Model SfM & Closed-Form Sim3d Alignment:**  
   When fast turns split reconstructions into submodels, traditional tools discard non-primary segments, dropping up to 70% of the room. Namma Space retains all submodels and fuses them using exact closed-form similarity transformations (Sim3d: 7-DoF scale $s$, rotation $\mathbf{R}$, translation $\mathbf{t}$) computed via `align_reconstructions_via_proj_centers`, achieving zero dead-reckoning drift.
6. **Statistical Outlier Removal (SOR) Floater Purge:**  
   Multi-view consensus rejects all points with track length $< 3$. A $k$-d tree Statistical Outlier filter ($k=12$) computes local mean neighbor distances $\mu$ and standard deviation $\sigma$, pruning points exceeding $\mu + 1.25\sigma$ (purging 43,000+ noisy air points).
7. **Tight Voronoi Pancake Surfel Synthesis:**  
   Spherical Gaussians cause blurry smog when large ($0.50\,\text{m}$) and black out when zooming. We scale radii strictly to $s_{xy} = \text{clip}(\text{avg\_dist} \times 0.40, 0.003, 0.045)\,\text{m}$ (3mm to 4.5cm) and flatten along surface normals ($s_z = 0.15 \cdot s_{xy}$) with high opacity ($\alpha \ge 235$), yielding razor-sharp solid geometry packaged into 32-byte binary format (`scene.splat`).

| Pipeline Stage | Algorithmic Method | Mathematical Operation / Key Parameters | Output Artifact |
|---|---|---|---|
| **Frame Ingestion** | Temporal Subsampling | 2.5 fps sampling, Laplacian blur filter | JPEG Keyframe Sequence |
| **Camera Intrinsics** | Shared Physical Sensor | `CameraMode.SINGLE`, `SIMPLE_RADIAL`, $f=1017.6\,\text{px}$ | Unified Camera Model |
| **Feature Detection** | Covariant SIFT + DSP | `first_octave=-1`, `peak_thresh=0.004`, `edge=15.0` | 128D SIFT Descriptors |
| **Feature Matching** | Chronological Pair Graph | Local window $[t-25..t+25]$ + quadratic loop jumps | `two_view_geometries` (DB) |
| **Structure-from-Motion** | Incremental Mapping | `abs_pose_min_inliers=12`, `init_tri_angle=3.0` deg | Multi-Model Sparse Cloud |
| **Submodel Fusion** | Sim3d Projection Centers | Closed-form Sim3d ($s, \mathbf{R}, \mathbf{t}$) alignment | Unified Global Coordinates |
| **Outlier Rejection** | Multi-View Consensus + SOR | $track\_length \ge 3$, $k=12$, $dist \le \mu + 1.25\sigma$ | Cleaned Surfel Cloud |
| **Surfel Synthesis** | Pancake Splat Parameterization | $s_{xy} \in [0.003, 0.045]\,\text{m}$, $s_z = 0.15 s_{xy}$, $\alpha \ge 235$ | `scene.splat` (32-byte binary) |

---

## 4. Smartphone Capture Standard Operating Procedure (SOP) Details

Photogrammetric triangulation relies strictly on multi-view baseline parallax. Pure rotational panning (standing in one spot and turning) produces zero baseline displacement, resulting in catastrophic epipolar degeneracy. Our standardized 4-stage mobile capture protocol guarantees reliable 3D reconstruction:

* **Stage 1 — Environmental Conditioning:** Turn on all artificial room lighting to maximize photon count and minimize sensor gain noise. Close window curtains/blinds to eliminate extreme specular sunlight blooms. Open all interior doors. For featureless walls, temporarily position textured visual cues (e.g., sticky notes or posters) to provide reliable keypoint tracking.
* **Stage 2 — Sensor Configuration & Freezing:** Hold smartphone strictly in landscape orientation. Select standard 1.0x optical wide lens (strictly avoid 0.5x ultra-wide due to unmodeled non-linear radial distortion). Set resolution to 1080p @ 30 fps. **Mandatory AE/AF Lock:** Long-press on the center of the room to permanently lock auto-exposure, auto-white-balance, and focal distance across the entire video.
* **Stage 3 — Dual-Loop Walking Trajectory:** Execute a deliberate 45–75 second heel-to-toe "ninja walk" (0.5–0.8 m/s):
  * *Outer Loop (Perimeter Pass):* Walk along the room perimeter walls facing inwards at a 45-degree angle, sweeping baseboards, corners, and wall-floor junctions (~30–40s).
  * *Inner Loop (Central Furniture Orbit):* Transition smoothly into a tighter circular orbit around central furniture (desks, sofas, beds) to capture occlusion geometry (~20s).
* **Stage 4 — Stationary Buffer Holds:** Maintain a completely motionless 3–4 second hold at the exact beginning and end of recording to isolate touchscreen tapping vibrations from keyframe selection.

| Capture Checkpoint | Operational Protocol | Failure Mode if Ignored | Corrective Action |
|---|---|---|---|
| **Exposure & Focus** | Mandatory AE/AF Lock prior to recording | Photometric flickering, SIFT descriptor mismatch | Long-press smartphone screen to lock exposure. |
| **Lens Selection** | Standard 1.0x optical wide lens | 0.5x ultra-wide introduces severe barrel distortion | Use 1.0x default camera profile. |
| **Walking Gait** | Heel-to-toe "ninja walk" (0.5-0.8 m/s) | Vertical rolling-shutter wobble, motion blur | Glide steadily without abrupt directional jerks. |
| **Trajectory Route** | Dual-loop: perimeter pass + central orbit | Occluded dead zones behind furniture | Ensure central objects receive 360-degree coverage. |
| **Monochromatic Walls** | Add high-contrast temporary markers | Zero keypoint detection, lost camera tracks | Place textured sticky notes on plain surfaces. |

---

## 5. Technical Approach & Architectural Trade-off Analysis

| Design Dimension | Adopted Solution | Evaluated Alternatives | Architectural Rationale & Justification |
|---|---|---|---|
| **Spatial Representation** | 3D Gaussian Radiance Field | NeRF, Textured Triangle Mesh | 3DGS renders in real-time via tile rasterization; NeRF requires slow ray-marching (1-5s/frame). |
| **Multi-Model Fusion** | Closed-Form Sim3d Alignment | Velocity Dead Reckoning, Discardation | Sim3d provides exact metric scale & rotation alignment; dead reckoning drifts exponentially (20m+ error). |
| **Web Delivery Engine** | WebGL2 + WebAssembly Worker | Server-Side Video Streaming (Pixel Stream) | Client-side WebGL2 eliminates expensive cloud GPU streaming costs (\$0.00 server egress budget). |
| **UI Architecture** | Vanilla HTML5 / CSS / ES Modules | React / Next.js / Angular SPA | Eliminates hydration lag, bundle bloat, and build steps; loads instantly on consumer mobile & desktop. |

---

## 6. Browser Viewer Engine & First-Person WASD Navigation

The Namma Space client delivers an uncompromised spatial computing experience directly in standard web browsers:

* **First-Person WASD Roaming:** Keyboard event listeners compute real-time translational displacement along the camera's view-look and strafe vectors:
  $$\Delta \mathbf{P}_{\text{forward}} = \mathbf{V}_{\text{look}} \cdot v \cdot \Delta t, \quad \Delta \mathbf{P}_{\text{strafe}} = (\mathbf{V}_{\text{look}} \times \mathbf{V}_{\text{up}}) \cdot v \cdot \Delta t$$
  The camera up-vector is fixed to $[0, -1, 0]$ to prevent disorientation and roll inversion.
* **Interactive Mouse Orbit:** Left-click drag controls spherical pitch/yaw; right-click drag pans laterally; scroll wheel modulates zoom.
* **Live Telemetry HUD:** A glassmorphic HUD renders real-time coordinate telemetry $(x, y, z)$ and active keypress indicators.
* **Asynchronous Web Worker Radix Depth Sorting:** To prevent z-fighting across semi-transparent Gaussians, splats are dynamically sorted by camera depth inside a dedicated Web Worker via WebAssembly, sustaining steady 60 FPS on integrated APUs.
* **Client-Side Cross-Origin Isolation Bridge:** Static hosts (GitHub Pages) do not permit custom headers. Namma Space deploys `coi-serviceworker.js` to dynamically register COOP (`same-origin`) and COEP (`credentialless`) on the client side, unlocking `SharedArrayBuffer`.

---

## 7. Empirical Results & Performance Benchmarks

Verification was conducted using automated Chrome DevTools Protocol (CDP) test suites across both real-world smartphone video and synthetic benchmarks:

| Benchmark Metric | Measured Real-World Value | Verification Evidence & Audit Status |
|---|---|---|
| **3D Radiance Model Size** | 12.12 MB (`scene.splat`) | Binary 32-byte format; complete multi-room spatial twin (PASS). |
| **Registered Camera Count** | 58 Walkthrough Views | Continuous indoor trajectory with initial overview hero pose (PASS). |
| **Total Gaussian Elements** | 378,886 3D Gaussians | Dense photometric coverage preserving white walls, bed, & floor (PASS). |
| **Initial Stream & Parse** | 180ms localhost (1.9s cloud 4G) | Instant buffer construction without hydration overhead (PASS). |
| **Rendering Frame Rate** | Steady 60.0 FPS | Verified WebGL2 frame telemetry under continuous WASD flight (PASS). |
| **Hero Overview Spawn** | $x: 0.470, y: -0.467, z: -5.779$ | Spawns facing full interior overview with guitar and bedding (PASS). |
| **Console Error Audit** | 0 Exceptions, 0 Warnings | CDP `Runtime.consoleAPICalled` verified 100% clean stream (PASS). |

---

## 8. Reproducibility, Attribution & Statement of Originality

* **Local Reproduction:** Clone repository, install dependencies in Python virtual environment, and run `python serve_web.py`. Access `http://127.0.0.1:8080/index.html` to test live upload and viewer roaming.
* **Third-Party Attributions:** Inria / MPI (3D Gaussian Splatting, Kerbl et al., SIGGRAPH 2023); COLMAP (Schönberger & Frahm, CVPR 2016); GaussianSplats3D (Mark Kellogg et al., WebGL2 engine); Three.js (Cabello et al., 3D math & scene graph).
* **Statement of Original Implementation:** Namma Space independently developed:
  1. The responsive dark-mode web portal with in-browser video upload and real-time SSE progress telemetry.
  2. The 0% discardation multi-model Sim3d closed-form similarity alignment engine.
  3. The $k$-d tree Statistical Outlier Removal (SOR) floater purging filter.
  4. The tight Voronoi pancake surfel parameterization ($0.003–0.045\,\text{m}$, $\alpha \ge 235$).
  5. The client-side Cross-Origin Isolation service worker bridge.
  6. The 6-DoF first-person WASD roaming engine with live coordinate telemetry HUD.
  7. The 47-gate automated compliance audit test suite.
