# Namma Space — Repository Audit: Roomsplat Engine

**Project:** Techfest IIT Bombay 2026–27 | Namma Space (Round 1)  
**Evaluated Repository:** [Roomsplat](https://github.com/Ahmedn1/roomsplat) (`Ahmedn1/roomsplat`)  
**Audit Date:** October 28, 2026  
**Auditor:** Antigravity Engineering Agent  

---

## 1. Executive Summary

Roomsplat is an end-to-end Python pipeline designed to convert standard smartphone walkthrough videos of indoor spaces into 3D Gaussian Splats viewable in modern web browsers without cloud dependencies.

The upstream repository provides an automated wrapper around:
1. **OpenCV** for frame extraction, temporal deduplication, and resolution scaling.
2. **COLMAP (via `pycolmap`)** or **MASt3R** for camera pose estimation (Structure-from-Motion).
3. **Inria Gaussian Splatting (`gaussian-splatting`)** for 3D radiance field training.
4. **NumPy / SciPy** for exporting trained Gaussian point clouds into compact `.splat` binary formats and `cameras.json` metadata.
5. **Three.js + `@mkkellogg/gaussian-splats-3d`** for client-side WebGL2 browser visualization.

### Key Strengths for Namma Space Round 1
- **Direct Fit for Competition Scope:** Tailored specifically for indoor phone walkthroughs, resolving common issues like plain walls, motion blur, and starting camera height.
- **Lightweight Web Delivery:** Generates compact `.splat` files (~10–15 MB) and `cameras.json` to place the initial view inside the room rather than outside bounds.
- **Client-Side WASD Roaming:** Embeds first-person navigation (orbit, pan, WASD fly controls, live camera coordinate HUD).

### Core Architectural Bottlenecks & Upstream Limitations
- **Strict CUDA Requirement:** The training submodule (`diff-gaussian-rasterization`) compiles C++/CUDA kernels and strictly requires an NVIDIA GPU with at least 8 GB VRAM.
- **POSIX / Linux Assumption:** `roomsplat/pipeline/train.py` relies on Linux path conventions (`/usr/local/cuda`, `/usr/bin/gcc-12`, `miniconda3/envs/.../bin/python`).
- **Windows Symlink Limitation:** `roomsplat/cli.py` attempts to symlink `scene.ply` into `viewer/scene.ply`, which fails on standard Windows installations without elevated administrative rights or Developer Mode.
- **Upstream License Constraints:** Inria 3DGS and NAVER MASt3R are strictly **non-commercial / research use only**. (Permissible for student hackathon research and academic evaluation, but commercial deployments require clean-room engines such as `gsplat` or Apache 2.0 alternatives).

---

## 2. Repository Layout & File Inventory

```
roomsplat/
├── .gitignore
├── LICENSE                         # MIT (wrapper); notes Inria & MASt3R non-commercial terms
├── README.md                        # Documentation, capture tips, hyperparameter recommendations
├── pyproject.toml                  # Python package configuration (Python >= 3.8)
├── docs/                           # Pre-built live demo & Netlify static hosting assets
│   ├── index.html                  # Demo web viewer
│   ├── scene.splat                 # 11 MB sample binary (Office scene, SH0 flat colour)
│   ├── cameras.json                # Poses from COLMAP training cameras
│   ├── _headers                    # COOP/COEP headers for Netlify
│   └── .nojekyll                   # GitHub Pages configuration
├── notebook/
│   ├── office_tour.ipynb           # Detailed ablation study, benchmark runs, lessons learned
│   └── *.png                       # Reconstruction metrics and trajectory diagrams
└── roomsplat/                      # Main Python package
    ├── __init__.py
    ├── cli.py                      # Typer CLI ('run', 'view', 'config')
    ├── config.py                   # Dependency resolution (~/.roomsplat/config.json)
    ├── pipeline/
    │   ├── __init__.py
    │   ├── extract.py              # OpenCV video frame extraction and downsampling
    │   ├── poses.py                # COLMAP & MASt3R camera pose estimation
    │   ├── train.py                # Inria gaussian-splatting training orchestrator
    │   └── export.py               # PLY -> .splat converter & cameras.json writer
    └── viewer/
        ├── __init__.py
        ├── serve.py                # Local Python HTTP server with COOP/COEP headers
        └── static/
            └── index.html          # Web viewer template with {{ROOM_NAME}} injection
```

---

## 3. The End-to-End Reconstruction Pipeline

```
[ Smartphone Video (.mp4 / .mov) ]
                 │
                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Step 1: Video Frame Extraction (`roomsplat/pipeline/extract.py`)
 │ • Trims first & last 5% to eliminate user start/stop motion.
 │ • Downsamples to target FPS (default 2.5 fps; recommended 0.8 fps).
 │ • Resizes longest edge to max_dim (default 1600px; max 1920px).
 │ • Skips static/near-duplicate frames (mean pixel difference < 0.02).
 └───────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Step 2: Camera Pose Estimation (`roomsplat/pipeline/poses.py`)
 │ Method A: COLMAP (`pycolmap`)
 │   - SIFT GPU feature extraction (up to 8,192 features/image).
 │   - Sequential matcher (window ±10 frames) or Exhaustive matcher.
 │   - Incremental SfM mapping -> outputs cameras.bin, images.bin, points3D.bin.
 │   - Optional radial undistortion (`--undistort`).
 │ Method B: MASt3R Deep-Learning SfM (Fallback for textureless walls)
 │   - Subsamples to <= 30 frames; runs pairwise Vision Transformer inference.
 │   - Global Point Cloud Alignment -> writes COLMAP-compatible binary files.
 └───────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Step 3: 3D Gaussian Splatting Training (`roomsplat/pipeline/train.py`)
 │ • Invokes external `gaussian-splatting/train.py` as an isolated subprocess.
 │ • Inputs: `images/` directory + `sparse/0/` COLMAP sparse reconstruction.
 │ • Optimizes 3D Gaussians (position, scale, rotation, opacity, spherical harmonics).
 │ • Standard: 30,000 iterations (~35–45 min on RTX 3080).
 │ • Fast preview: 7,000 iterations (~5 min).
 │ • Output: `point_cloud/iteration_30000/point_cloud.ply`.
 └───────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Step 4: Scene Export (`roomsplat/pipeline/export.py`)
 │ • Converts `point_cloud.ply` into 32-byte `.splat` binary format.
 │ • Layout per Gaussian: [xyz f32*3] [scale f32*3] [rgba u8*4] [rot u8*4].
 │ • Sorts Gaussians descending by opacity for early web culling.
 │ • Extracts camera centers and forward vectors from `images.bin` into `cameras.json`.
 │ • Optional: generates `.splat.sh` sidecar for full SH3 view-dependent color.
 └───────────────────────────────┬─────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ Step 5: Web Viewer Generation & Delivery (`roomsplat/viewer/`)
 │ • Injects room name into `viewer/static/index.html`.
 │ • Starts local HTTP server (`roomsplat/viewer/serve.py`) on port 8080.
 │ • Injects headers:
 │   - `Cross-Origin-Opener-Policy: same-origin`
 │   - `Cross-Origin-Embedder-Policy: require-corp` (or `credentialless`)
 │ • Launches browser; `@mkkellogg/gaussian-splats-3d` renders scene via WebGL2.
 └─────────────────────────────────────────────────────────────┘
```

---

## 4. Upstream CLI & Operational Commands

### A. Environment Configuration
```bash
# Configure pointers to external repositories
roomsplat config --gs-dir /path/to/gaussian-splatting
roomsplat config --mast3r-dir /path/to/mast3r
roomsplat config --show
```

### B. Full Reconstruction Pipeline
```bash
# Standard pipeline run
roomsplat run video.mp4 --name "Living Room"

# Recommended settings for indoor rooms (from office_tour.ipynb ablation)
roomsplat run video.mp4 \
  --name "Namma Space Room" \
  --fps 0.8 \
  --max-dim 1600 \
  --pose-method colmap \
  --camera-model SIMPLE_RADIAL \
  --matcher exhaustive \
  --iterations 30000 \
  --sh-degree 3

# Fast preview run (low iteration budget)
roomsplat run video.mp4 --iterations 7000 --no-view
```

### C. Viewing an Existing Scene
```bash
# Launch built-in HTTP server and open browser
roomsplat view path/to/output_splat/ --port 8080
```

---

## 5. Viewer Architecture & Interactive Controls

### A. Rendering Library
- **Engine:** `@mkkellogg/gaussian-splats-3d` (version 0.4.6) running over **Three.js** (version 0.170.0).
- **Format Support:**
  - `.splat`: 32-byte binary format containing position, scale, RGBA (SH0), and quaternion rotation.
  - `.ply`: Full standard Gaussian Splatting PLY format containing higher-order spherical harmonics (SH2/SH3 view-dependent effects).
- **Web Workers:** Employs Web Workers with `SharedArrayBuffer` for fast depth-sorting of splats during camera movement.

### B. Controls & Navigation
- **Orbit:** Left-click drag.
- **Pan:** Right-click drag.
- **Zoom:** Mouse scroll wheel.
- **First-Person Fly Roaming:** `W`, `A`, `S`, `D` keys for translational motion.
- **Camera Pose Initialization:** On startup, reads `cameras.json` and places the camera at `camPos` looking towards `camLookAt`, ensuring the initial view originates from a real capture point rather than empty space.
- **Real-time HUD:** Displays current live camera world coordinates `(x, y, z)` at the bottom left.

---

## 6. Dependency & License Analysis

| Component | Source / Package | License | Distribution & Hackathon Validity |
|---|---|---|---|
| **Roomsplat CLI & Pipeline** | `roomsplat` | MIT License | Fully open-source; free to adapt and build upon. |
| **CLI & UI Utilities** | `typer`, `rich` | MIT License | Permissive. |
| **Computer Vision Core** | `opencv-python-headless`, `scipy`, `numpy` | Apache 2.0 / BSD | Permissive. |
| **Point Cloud Processing** | `plyfile` | GNU GPL v3 | Standard PLY reading utility. |
| **Structure-from-Motion** | `pycolmap` / COLMAP | BSD 3-Clause | Permissive for research and evaluation. |
| **3DGS Optimization** | `gaussian-splatting` (Inria) | **Inria Research / Non-Commercial** | Strictly non-commercial. Acceptable for academic competition / hackathon research. |
| **Rasterizer Extension** | `diff-gaussian-rasterization` | **Inria Custom / Non-Commercial** | Requires CUDA C++ compilation. |
| **Deep SfM Fallback** | `naver/mast3r` | **CC BY-NC-SA 4.0** | Optional; non-commercial only. |
| **Client WebGL Viewer** | `@mkkellogg/gaussian-splats-3d` | MIT License | Permissive; production-ready for web delivery. |

---

## 7. Conclusions & Compatibility Verdict

1. **Reconstruction Pipeline:** Highly competent, incorporating critical indoor-specific adaptations (anti-blur deduplication, radial distortion compensation, and initial pose alignment).
2. **Local Execution Feasibility:** Roomsplat's reconstruction stage cannot run locally on machines lacking an NVIDIA GPU or running Python versions lacking CUDA wheel support.
3. **Web Viewer Decoupling:** The browser viewer (`index.html` + Three.js + WebAssembly sort worker) is completely decoupled from the training pipeline. It runs on any standard client browser with WebGL2 support.
