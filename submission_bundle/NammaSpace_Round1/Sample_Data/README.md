# Test Datasets Directory — Namma Space

This directory houses test video footage and sample datasets for the Namma Space 3D reconstruction pipeline.

## Directory Structure
- `sample_walkthrough/`
  - `sample_synthetic_walkthrough.mp4` (1.81 MB): A 10.0-second synthetic marker animation (640×480 @ 30 fps) used for lightweight end-to-end integration testing of OpenCV frame extraction and COLMAP pose estimation.
- `real_room/` (Target Directory for User Capture)
  - `my_room_walkthrough.mp4`: Placeholder destination for the genuine smartphone room walkthrough video recorded following `docs/CAPTURE_SOP.md`.

## Data Governance & Licensing
- Large intermediate training caches (`colmap_workspace/`, `model/`, `*_splat/`) are strictly excluded from version control via `.gitignore`.
- Raw phone videos committed here should remain under 50 MB to comply with Git repository constraints.
