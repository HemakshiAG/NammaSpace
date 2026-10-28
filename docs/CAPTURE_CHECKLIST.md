# Smartphone Indoor Capture Checklist & Pre-Processing Quality Gate

**Project:** Techfest IIT Bombay 2026–27 | Namma Space (Round 1)  
**Document ID:** `CHK-CAP-001`  
**Companion Document:** [docs/CAPTURE_SOP.md](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/docs/CAPTURE_SOP.md)  
**Format:** Field-ready printable & digital inspection checklist  

---

## How to Use This Checklist
Follow these checklist items in sequence before, during, and immediately after recording your indoor walkthrough video. Do not proceed to cloud 3DGS training until all criteria in Phase 4 and Phase 5 pass inspection.

> [!NOTE]
> Numerical targets in this checklist (such as overlap percentages, capture durations, and registration thresholds) are engineering recommendations derived from empirical testing with Roomsplat and COLMAP. They represent best-practice benchmarks that should be validated and adapted to your specific room geometry.

---

## Phase 1: Room Selection & Physical Conditioning

Complete these checks before unlocking your smartphone camera.

- [ ] **Room Size & Layout:** Target room is an enclosed space between 10 m² and 45 m² with clear walking paths around furniture.
- [ ] **Physical Decluttering:** Transient floor and surface clutter (cables, loose laundry, garbage bins, food items, scattered papers) has been removed.
- [ ] **Path Clearance:** Walking path along the perimeter walls and between interior furniture is completely unobstructed and free of trip hazards.
- [ ] **Zero Scene Motion:**
  - [ ] Ceiling fans, standing fans, and portable heaters are turned **OFF**.
  - [ ] All windows and exterior doors are closed to prevent wind from moving curtains or papers.
  - [ ] All pets and occupants have exited the room; the door is shut.
- [ ] **Lighting Stabilization:**
  - [ ] All artificial room lights (ceiling fixtures, desk lamps) are switched **ON**.
  - [ ] Window blinds or curtains are drawn to eliminate harsh direct sunlight glare, shafts, and shifting clouds.
  - [ ] No flickering LED fixtures or strobing lights are present.
- [ ] **Reflective Surfaces & Glass Addressed:**
  - [ ] Large mirrors are either covered with a matte cloth or patterned sheets, or the walking trajectory is planned to avoid filming direct reflections.
  - [ ] Highly reflective glass cabinet doors or windows are masked or curtained.
- [ ] **Featureless Wall Mitigation:**
  - [ ] Large, plain, solid-color painted walls have high-contrast visual anchors (temporary patterned posters, newspaper pages, framed prints, or furniture corners positioned in front of them).
  - [ ] No plain bare wall occupies more than 60% of the camera view in any single frame.

---

## Phase 2: Smartphone & Camera Configuration

Set your phone settings strictly according to photogrammetry requirements.

- [ ] **Camera App:** Standard native phone camera app (iOS Camera / Android Camera) in standard **Video** mode (do not use "Cinematic", "Portrait", or "Slow Motion").
- [ ] **Orientation:** Phone is held strictly in **Landscape Mode (Horizontal)**.
- [ ] **Resolution & Frame Rate:** Set to **1080p (Full HD) at 30 fps** (or 60 fps if 30 fps is unavailable).
- [ ] **Lens Selection:** Set to standard **1.0× Wide Lens**.
  - [ ] **NO Ultra-Wide (0.5× / 0.6×)** lens enabled (avoids optical edge distortion).
  - [ ] **NO Telephoto (2× / 3× / 5×)** or digital zoom enabled.
- [ ] **Exposure & Focus Lock (AE/AF Lock):**
  - [ ] Tapped and held on a neutral surface in the room until **"AE/AF LOCK"** appears on the screen.
  - [ ] Verified that panning the phone across the room does *not* cause automatic brightness jumps or focus hunting.
- [ ] **Hardware Preparedness:**
  - [ ] Camera lenses physically cleaned with a microfiber cloth to remove fingerprint smudges and light halos.
  - [ ] Smartphone has at least 2 GB of free storage space.
  - [ ] Battery level is at least 30%.

---

## Phase 3: Trajectory & In-Flight Walking Protocol

Follow this physical protocol during the actual capture.

- [ ] **Starting Position:** Operator stands at the room entrance doorway facing into the room.
- [ ] **Ergonomic Grip:** Phone is held securely with **both hands at chest level**, elbows tucked against ribs for mechanical stability.
- [ ] **Initial 3-Second Stationary Anchor:**
  - [ ] Tapped Record.
  - [ ] Stood **completely motionless for 3 to 4 seconds** before taking the first step (buffers against screen-tap shake).
- [ ] **Walking Mechanics ("Ninja Walk"):**
  - [ ] Knees slightly bent to absorb walking vibration.
  - [ ] Smooth heel-to-toe foot rolling.
  - [ ] Continuous, steady walking pace of **0.5 to 0.8 meters/second** (approx. half normal walking speed).
- [ ] **Translation Over Rotation:**
  - [ ] Camera is physically translated by walking through space.
  - [ ] No standing in one spot and pivoting/spinning on heels.
- [ ] **Two-Loop Trajectory Execution:**
  - [ ] **Loop 1 (Perimeter):** Walked along perimeter walls, angling camera smoothly at ~30°–45° toward walls, doors, and corners.
  - [ ] **Corner Navigation:** Slowed down at room corners, tracing a smooth curved arc rather than snapping abruptly.
  - [ ] **Loop 2 (Interior Orbit):** Walked an interior loop around central furniture (bed/desk/table), angling camera inward to capture tops, sides, and occluded legs.
- [ ] **Visual Overlap Maintenance:**
  - [ ] Adjacent viewpoints share ~60% to 70% visible features (objects drift gradually across the screen over 3–5 steps).
- [ ] **Loop Closure:**
  - [ ] Walked back to the exact initial entrance position.
- [ ] **Final 3-Second Stationary Anchor:**
  - [ ] Stood **completely motionless for 3 to 4 seconds** at the starting point.
  - [ ] Tapped Stop without jerking the phone.
- [ ] **Duration Check:** Total recording duration is between **45 and 90 seconds** (recommended for standard single rooms).

---

## Phase 4: Immediate On-Device Video Review

Inspect the recorded video on your phone screen before leaving the physical room. If any test fails, re-record immediately while the room is prepared.

| Inspection Item | What to Look For | Pass Criteria | Fail / Retake Trigger |
|---|---|---|---|
| **1. Motion Blur** | Pause the video at 5 random points during walking. Zoom in on a picture frame, text, or furniture edge. | Edges, text, and wood grains are crisp and sharply readable. | Noticeable motion streak or blurry double edges on objects. |
| **2. Exposure Shifts** | Scrub through the entire video quickly. Watch the overall room brightness. | Brightness remains completely stable throughout the video. | Screen pulses darker or brighter when passing lamps or windows. |
| **3. Focus Hunting** | Watch fine details as the distance to objects changes during the walk. | Focus remains locked at mid-depth across all frames. | Camera lens visibly pulses in and out attempting to autofocus. |
| **4. Panning Snap** | Watch the horizon and corner transitions. | Camera moves in continuous, fluid, sweeping lines. | Operator stopped, rotated rapidly in place, or tilted abruptly. |
| **5. Start/End Shake** | Check the very beginning and very end of the video. | A clear 3-second motionless freeze exists at both ends. | Operator was walking while tapping start, or jerked phone while tapping stop. |
| **6. Duration & Size** | Check video file properties in Gallery/Photos. | Duration is 45s–90s; file size is typically 100 MB–350 MB. | Video is < 30s (too fast, high blur) or > 150s (excessive redundant frames). |

---

## Phase 5: Automated Pre-Processing Quality Gate (Rejection Criteria)

Before dispatching the video to remote GPU training (which consumes compute quota and takes 30–60 minutes), validate the recording against these programmatic rejection gates:

```
[ Captured Video: input_walkthrough.mp4 ]
                     │
                     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ GATE 1: Video File Integrity Check                          │
  │ • File is readable by OpenCV (cv2.VideoCapture).            │
  │ • Resolution >= 1280x720, FPS >= 24.0.                      │
  │ • Duration >= 35s and <= 120s.                              │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ PASS
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ GATE 2: Frame Extraction & Deduplication Check              │
  │ • Roomsplat extract.py runs cleanly at 0.8–2.5 fps.         │
  │ • Number of deduplicated frames is between 80 and 250.      │
  │ • Automated 5% start/end trim removes all boundary shake.   │
  └──────────────────────────────┬──────────────────────────────┘
                                 │ PASS
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ GATE 3: Quick SIFT Feature Density Check                    │
  │ • Run pycolmap feature extraction on first 5 frames.        │
  │ • Extracted SIFT features per frame > 1,500.                │
  │   (If < 1,000: room has insufficient texture / bad lighting)│
  └──────────────────────────────┬──────────────────────────────┘
                                 │ PASS
                                 ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ GATE 4: Sparse Reconstruction Registration Gate             │
  │ • Run pycolmap sequential SfM (Step 2 of Roomsplat).        │
  │ • Registration Rate: >= 80% of extracted frames registered.  │
  │ • Reconstructed Points: >= 1,000 sparse 3D points.          │
  └──────────────────────────────┬──────────────────────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           │ PASS (>= 80% registered)                  │ FAIL (< 80% registered)
           ▼                                           ▼
 ┌───────────────────────────────────┐       ┌───────────────────────────────────┐
 │ PROCEED TO FULL 3DGS TRAINING     │       │ REJECT RECORDING OR FALLBACK:     │
 │ • Run 30,000 iterations on Colab  │       │ 1. Switch to --matcher exhaustive │
 │ • High confidence of clean scene  │       │ 2. Switch to --pose-method mast3r │
 │   reconstruction & accurate poses │       │ 3. If still fails: Re-record room │
 └───────────────────────────────────┘       └───────────────────────────────────┘
```

### Programmatic Rejection Criteria Summary Table

| Gate ID | Check Name | Programmatic Condition | Action if Failed |
|---|---|---|---|
| **GATE-01** | **Frame Count Check** | Extracted frames (`n_frames`) < 60 | **REJECT:** Walk was too brief or moved too quickly. Re-record at slower walking speed. |
| **GATE-02** | **Excessive Duplication**| Deduplication drops > 75% of frames | **REJECT:** Operator stood in place too long. Re-record with continuous movement. |
| **GATE-03** | **SIFT Density Gate** | Average features/frame < 1,000 | **REJECT:** Insufficient texture or blurry frames. Increase room lighting, clean lens, and add wall anchors. |
| **GATE-04** | **COLMAP Registration Gate** | Registered frames (`registered / n_frames`) < 80% | **ACTION REQUIRED:** Attempt exhaustive matching (`--matcher exhaustive`). If registration remains < 80%, re-record following trajectory guidelines. |
| **GATE-05** | **Sparse Point Count**| Reconstructed 3D points < 800 | **REJECT:** Geometry failed to triangulate. Room lacked visual overlap. |
| **GATE-06** | **Trajectory Disconnection**| COLMAP creates multiple disconnected models (`sparse/1`, `sparse/2`) | **REJECT:** Camera moved too fast across a doorway or corner, breaking visual continuity. Re-record with smoother corner curves. |

---

## Final Verification Sign-Off

Before uploading the video to Google Colab or Kaggle for 30,000-iteration radiance field training, confirm:

- [ ] All Phase 1, Phase 2, and Phase 3 checks were verified on-site.
- [ ] On-device playback inspection (Phase 4) passed without motion blur or lighting shifts.
- [ ] Preliminary COLMAP registration (Phase 5 Gate 4) achieved **≥ 80% camera registration**.

**Record Name:** `________________________________________`  
**Capture Operator:** `____________________________________`  
**Date & Time:** `________________________________________`  
**Pass / Fail Verdict:** `[  ] PASS — Ready for 3DGS Training    [  ] FAIL — Re-recording Required`
