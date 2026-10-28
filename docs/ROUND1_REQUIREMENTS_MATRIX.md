# Techfest IIT Bombay 2026–27 | Namma Space
## Round 1 Requirements & Compliance Matrix

**Competition:** Techfest IIT Bombay 2026–27 — Namma Space  
**Round:** Round 1 (3D Reconstruction & Roaming)  
**Status Date:** October 28, 2026  
**Auditor:** Antigravity Engineering Agent  

---

## 1. Requirements Compliance Matrix

| ID | Requirement Category | Specific Requirement | Current Status | Technical Evidence & Current State | Next Action Needed |
|:---|:---|:---|:---:|:---|:---|
| **REQ-01** | **Data Ingestion** | Capture a real indoor space using standard smartphone video (following SOP: continuous path, ~60% overlap, translational motion, even lighting). | 🟡 **PENDING USER CAPTURE** | No custom indoor video has been captured or ingested yet. The repository currently holds only the upstream demo reference (`Ahmedn1/roomsplat`). | Record a 45–75 second walkthrough of a real target room following the capture guidelines; place raw video in `data/raw_video.mp4`. |
| **REQ-02** | **Frame Extraction** | Automated frame sampling, downsampling (longest edge 1600–1920px), and deduplication/blur filtering. | 🟢 **SATISFIED (Code)** | Implemented in `roomsplat/pipeline/extract.py`. Uses OpenCV with frame-difference filtering (`skip_similar_threshold=0.02`) and start/end trimming. | Run frame extraction script on the captured video in a Python 3.10+ environment. |
| **REQ-03** | **Camera Pose Estimation** | Structure-from-Motion (SfM) recovering extrinsic/intrinsic camera matrices and sparse 3D point cloud. | 🟡 **BLOCKED LOCALLY / SATISFIED VIA CLOUD** | Implemented in `roomsplat/pipeline/poses.py` via `pycolmap` and `MASt3R`. Blocked on local machine (requires CUDA GPU and Python <= 3.12). | Execute pose estimation on Google Colab or Kaggle NVIDIA T4 GPU instance. |
| **REQ-04** | **3D Gaussian Splatting Training** | Train a 3D Gaussian radiance field representation of the indoor space. | 🟡 **BLOCKED LOCALLY / SATISFIED VIA CLOUD** | Implemented in `roomsplat/pipeline/train.py` wrapping Inria `gaussian-splatting`. Blocked locally (host has AMD Radeon 740M APU, 512MB VRAM; requires NVIDIA GPU >= 8GB VRAM). | Run 30k iteration training on Colab/Kaggle T4 GPU using the captured frame/pose dataset. |
| **REQ-05** | **Binary Scene Export** | Convert heavy point cloud PLY to compact, web-optimized `.splat` binary (< 20 MB) and generate `cameras.json`. | 🟢 **SATISFIED (Code)** | Implemented in `roomsplat/pipeline/export.py`. Packs 32-byte splats and exports camera trajectory metadata. | Run export script on trained `point_cloud.ply` to produce `scene.splat` and `cameras.json`. |
| **REQ-06** | **Interactive 3D Web Viewer** | Modern, responsive browser-based 3D viewer capable of rendering the reconstructed scene. | 🟢 **SATISFIED (Code)** | Implemented in `roomsplat/viewer/static/index.html` using Three.js and `@mkkellogg/gaussian-splats-3d` (v0.4.6). Loads `.splat` and initializes at realistic camera pose. | Integrate the generated `scene.splat` and `cameras.json` into the production viewer directory. |
| **REQ-07** | **First-Person Roaming Navigation** | Desktop roaming controls supporting free exploration (WASD keyboard movement, mouse look, orbit/pan). | 🟢 **SATISFIED (Code)** | Viewer includes WASD fly navigation, mouse orbit/pan, and real-time XYZ camera coordinate HUD. | Polish viewer UX: add responsive instructions overlay, mobile touch fallback, and walking height constraint. |
| **REQ-08** | **Public Accessibility & Deployment** | Viewer must be publicly accessible via a live web URL (e.g. Netlify, Vercel, GitHub Pages) with required headers. | 🟡 **READY FOR DEPLOYMENT** | Header configuration file `docs/_headers` (`Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Embedder-Policy: credentialless`) is verified. Not yet deployed to a public hosting domain. | Deploy static viewer to Netlify / GitHub Pages once the genuine scene is exported. |
| **REQ-09** | **Round 1 Deliverables: Technical Abstract** | Written technical abstract explaining methodology, capture SOP, SfM accuracy, Gaussian count, and performance. | 🔴 **UNIMPLEMENTED** | No abstract document written yet. | Draft structured Technical Abstract following competition template once training metrics are collected. |
| **REQ-10** | **Round 1 Deliverables: Code Repository** | Clean, well-documented GitHub repository with installation instructions and pipeline reproducibility. | 🟡 **IN PROGRESS** | Workspace initialized with git remote pointing to `HemakshiAG/NammaSpace`. Upstream audit complete. | Commit clean audit documentation and setup instructions to `NammaSpace`. |
| **REQ-11** | **Round 1 Deliverables: Proof-of-Concept Web Link** | Active public URL allowing judges to interactively roam the reconstructed 3D twin in real time. | 🟡 **PENDING DEPLOYMENT** | Awaiting deployment of the team's genuine reconstructed room. | Provide live Netlify / Vercel link in submission abstract. |
| **REQ-12** | **Round 1 Deliverables: 3–5 Min Roaming Video** | Video recording demonstrating first-person free-roaming, fidelity from multiple angles, and coordinate telemetry. | 🔴 **UNIMPLEMENTED** | Cannot record video until genuine scene viewer is live. | Screen-record high-frame-rate roaming session with live telemetry once viewer is deployed. |

---

## 2. Gap Analysis Summary

```
COMPLETED / VERIFIED:
  [x] Pipeline architecture and code modules validated
  [x] WebGL2 viewer with WASD roaming verified
  [x] Format conversion (.ply -> .splat, cameras.json) verified
  [x] Netlify COOP/COEP header configuration verified

CURRENT GAPS / BLOCKERS:
  [!] Machine limitation: Local PC cannot run COLMAP GPU or Inria 3DGS training (No NVIDIA GPU, 512MB VRAM).
  [!] Real video capture: Target indoor space must be filmed following SOP.
  [!] Cloud training setup: Colab/Kaggle notebook needed to execute the genuine reconstruction.
  [!] Public deployment: Static web viewer needs to be deployed to a live URL.
  [!] Submission deliverables: Technical Abstract and 3-5 min demo video must be produced.
```

---

## 3. Recommended Smallest Viable Implementation Plan (SVIP)

To deliver a genuine, competitive, and compliant Round 1 submission without violating competition rules or wasting resources, execute the following four-phase plan:

```
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 1: TARGET CAPTURE & VIDEO INGESTION                │
└────────────────────────────────────────────────────────────────────────┘
  1. Select a well-lit, furnished indoor room (e.g. living room, lab, or office).
  2. Film a 45–75 second continuous walkthrough video (1080p @ 30fps):
     - Keep camera at eye level, moving at slow walking pace.
     - Ensure 60–70% overlap between adjacent views.
     - Move along translational paths (avoid stationary panning).
     - Add decorative or high-contrast anchors to plain bare walls.
  3. Save video as `target_room.mp4`.

                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 2: CLOUD RECONSTRUCTION (Colab / Kaggle)            │
└────────────────────────────────────────────────────────────────────────┘
  1. Launch a free Google Colab or Kaggle Notebook with NVIDIA T4 GPU (16 GB VRAM).
  2. Clone Roomsplat and install dependencies (`pycolmap`, `gaussian-splatting`).
  3. Upload `target_room.mp4` and run:
     ```bash
     roomsplat run target_room.mp4 \
       --name "Namma Space Twin" \
       --fps 0.8 \
       --max-dim 1600 \
       --matcher exhaustive \
       --iterations 30000 \
       --sh-degree 3 \
       --no-view
     ```
  4. Collect training statistics:
     - Number of extracted frames & COLMAP registration %
     - Gaussian count & training duration
     - Final loss / scale ratio metrics
  5. Download generated `viewer/` package containing:
     - `scene.splat` (~10–15 MB)
     - `cameras.json`
     - `point_cloud.ply` (for high-fidelity archiving)

                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 3: VIEWER REFINEMENT & PUBLIC DEPLOYMENT           │
└────────────────────────────────────────────────────────────────────────┘
  1. Commit `scene.splat`, `cameras.json`, and viewer assets to `docs/` or `web/`.
  2. Test viewer locally on the Windows workstation (`npx serve` or Python HTTP).
  3. Ensure first-person roaming (WASD + mouse), camera HUD, and initial viewpoint work flawlessly.
  4. Deploy to Netlify / Vercel with COOP/COEP headers enabled.
  5. Verify the live URL is globally accessible across Chrome, Edge, and mobile browsers.

                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────┐
│               PHASE 4: SUBMISSION ARTIFACTS COMPLETION                 │
└────────────────────────────────────────────────────────────────────────┘
  1. Record a 3–5 minute high-definition screen capture showing:
     - Free-roaming walkthrough from entrance to key room features.
     - WASD navigation and coordinate HUD in real time.
     - Visual fidelity comparison under different angles.
  2. Write the Round 1 Technical Abstract covering:
     - Pipeline methodology (video -> COLMAP SfM -> 3DGS -> .splat).
     - Hyperparameter choices and memory optimizations.
     - Quantitative results (frame count, registration rate, Gaussian count, load time).
  3. Submit the GitHub repository, public web link, abstract PDF, and video link.
```
