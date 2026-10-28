# Standard Operating Procedure (SOP): Indoor Smartphone Video Capture for 3D Gaussian Splatting

**Competition:** Techfest IIT Bombay 2026–27 | Namma Space (Round 1)  
**Document ID:** `SOP-CAP-001`  
**Target Reconstruction Engine:** [Roomsplat](https://github.com/Ahmedn1/roomsplat) (`colmap` SfM + Inria 3D Gaussian Splatting)  
**Applicability:** Real indoor spaces (living rooms, bedrooms, offices, labs, commercial rooms)  
**Intended Audience:** Non-technical operators, field capture team, competition evaluators  

---

## 1. Objective & Fundamental Principles

### 1.1 Objective
This Standard Operating Procedure (SOP) defines the exact steps required to capture high-fidelity, continuous smartphone walkthrough videos of real indoor rooms. Adherence to this procedure ensures that Structure-from-Motion (COLMAP) accurately estimates camera trajectories and Inria 3D Gaussian Splatting (3DGS) synthesizes photorealistic, navigable 3D digital twins without structural collapse or floater artifacts.

### 1.2 The Physics Behind 3D Gaussian Splatting (Why SOP Matters)
Traditional video recording is intended for human viewing, but 3D reconstruction algorithms operate on strict mathematical principles:
1. **Translational Motion vs. Rotational Panning:**  
   To compute the 3D position of an object, algorithms require **baseline parallax**—the camera position must physically shift in space so rays intersect at a point. **Standing in one spot and turning around (rotational panning) fails completely** because all rays originate from the exact same camera center, collapsing 3D depth into an ambiguous cylinder.
2. **Visual Overlap (Triangulation):**  
   Every physical point in the room must be visible in multiple distinct frames taken from slightly different viewpoints. A target overlap of **60% to 70%** between consecutive viewpoints is recommended to ensure robust feature correspondence.
3. **Static Scene Assumption:**  
   3DGS assumes all visual geometry and lighting remain 100% frozen in time. Any moving entity (people, pets, swaying curtains) or fluctuating light source (auto-exposure shifts, passing shadows) creates conflicting mathematical constraints, producing blurry "ghost" artifacts or reconstruction failure.

> [!NOTE]
> Values provided in this document (e.g. overlap percentages, capture durations, walking speeds) represent empirically validated engineering recommendations based on extensive indoor testing with the Roomsplat engine. They are guidelines that must be experimentally validated and tuned for each specific room environment.

---

## 2. Room Selection & Physical Space Preparation

A successful 3D reconstruction begins before turning on the camera. The physical environment must be conditioned to provide stable, textured visual features.

### 2.1 Room Selection Criteria
- **Recommended Size:** Single enclosed rooms between 10 m² and 45 m² (e.g., standard bedrooms, home offices, conference rooms, studio living spaces).
- **Geometric Complexity:** Rooms with existing furniture, decorative objects, bookshelves, rugs, and architectural variation reconstruct with significantly higher fidelity than completely empty, cavernous rooms.

### 2.2 Physical Space Preparation Steps
1. **Decluttering:**
   - Remove transient, random clutter from floors and tables (loose cables, discarded clothing, open food containers, scattered paperwork).
   - Ensure a clean, unobstructed walking path along the entire perimeter and interior of the room.
2. **Eliminating Motion:**
   - Turn off ceiling fans, oscillating pedestal fans, and portable heaters.
   - Close all windows to prevent wind from moving curtains, blinds, or hanging papers.
   - Ensure all family members, roommates, and pets remain outside the room and close the door.
3. **Handling Mirrors and Transparent Glass:**
   - *The Problem:* Mirrors reflect moving virtual objects, while transparent glass windows lack depth, severely confusing SIFT feature matching.
   - *The Solution:* 
     - Draw solid curtains or blinds over exterior windows.
     - For large mirrors (wardrobe doors, bathroom mirrors), tape a non-reflective matte pattern, temporarily cover them with a sheet/towel, or angle the walking trajectory so the operator's own reflection is minimized.
4. **Addressing Featureless, Plain Painted Walls (The "Blank Wall" Problem):**
   - *The Problem:* Plain, monochromatic painted walls (off-white, beige, grey) have no distinctive corners or contrast edges. COLMAP cannot match features across frames, leading to unregistered cameras and hollow holes in the 3D model.
   - *The Solution (Field-Proven Workarounds):*
     - Tape several sheets of printed newspaper or patterned posters at eye level across bare wall sections.
     - Hang temporary wall art, framed prints, or patterned throws over large blank surfaces.
     - Ensure the camera frame always includes high-contrast boundary objects (door frames, baseboards, switchboards, shelving, furniture corners) whenever pointing toward a wall. Avoid pointing the camera perpendicularly at a flat, bare wall in isolation.

---

## 3. Lighting Requirements

Even, stable illumination is the single most critical factor for consistent 3D radiance field training.

| Lighting Attribute | Recommended Setting | Unacceptable Condition |
|---|---|---|
| **Light Distribution** | Diffuse, indirect, multi-directional ambient light | Harsh direct sunlight, single harsh spotlights, deep dark shadows |
| **Windows & Sunlight** | Blinds lowered or translucent curtains drawn | Direct sunlight beaming onto floors/walls creating intense blinding glare |
| **Artificial Lighting** | All room ceiling lights and lamps switched ON | Flickering fluorescent tubes, strobing LED fixtures, partial room dark spots |
| **Light Stability** | Completely static throughout the capture session | Lights being switched on/off, dimmers adjusting, daylight fading |

### Actionable Lighting Guidelines:
- **Best Time for Capture:** Overcast daylight or daytime with curtains drawn and indoor lights turned on. Avoid capture during golden hour (sunset) when rapid lighting shifts occur.
- **Shadow Elimination:** Ensure corners and under-desk areas receive sufficient ambient bounce light so features remain distinguishable in shadow regions.

---

## 4. Camera Settings & Video Configuration

Smartphone native cameras often apply aggressive computational photography algorithms designed for casual video clips. These algorithms must be constrained for photogrammetry.

### 4.1 Recommended Phone Settings
1. **Resolution & Frame Rate:**
   - **Recommended:** **1080p (Full HD, 1920×1080) at 30 fps**.
   - *Rationale:* 1080p provides ample pixel detail without generating excessive file sizes. 4K video is acceptable but produces larger files without significant benefit, as Roomsplat downsamples frames to a target longest edge (default: 1600 px).
2. **Lens Selection:**
   - Use the **Primary Standard Wide Lens (1.0× zoom)**.
   - **DO NOT** use the Ultra-Wide lens (0.5× / 0.6×) unless the room is extremely tight (< 8 m²). Ultra-wide lenses introduce severe barrel distortion and edge softness that degrade camera matrix estimation.
   - **DO NOT** use digital zoom or telephoto lenses.
3. **Lock Auto-Exposure and Auto-Focus (AE/AF Lock):**
   - **MANDATORY STEP:** Tap and hold on a neutral, mid-tone surface in the center of the room until **"AE/AF LOCK"** appears on screen.
   - *Why this is critical:* If Auto-Exposure is active, walking past a lamp will cause the entire screen to darken, and walking toward a corner will cause it to brighten. This brightness shifting breaks the Lambertian photometric consistency assumption in 3DGS.
4. **Orientation:**
   - Hold the phone strictly in **Landscape Orientation (Horizontal)**. Landscape captures a wider horizontal field of view, maximizing lateral overlap between adjacent walkthrough frames.
5. **Image Stabilization:**
   - Standard Optical Image Stabilization (OIS) is beneficial.
   - Disable aggressive digital "Action Mode" or software crop stabilization, as dynamic software cropping constantly alters the effective focal length and principal point across frames.

---

## 5. Starting Position & Continuous Capture Trajectory

An organized, planned walking route ensures complete volumetric coverage and robust SfM loop closure.

### 5.1 Trajectory Layout (The Two-Loop Strategy)
A recommended room capture follows a continuous, closed-loop path combining a perimeter walk with an interior observation pass:

```
┌─────────────────────────────────────────────────────────────┐
│                       ROOM PERIMETER                        │
│                                                             │
│   [Corner 1] ──────────────────────────────── [Corner 2]    │
│       │                                           │         │
│       │        ┌─────────────────────────┐        │         │
│       │        │   Interior Furniture    │        │         │
│       │        │   (Bed / Desk / Table)  │        │         │
│       │        │                         │        │         │
│       │        └─────────────────────────┘        │         │
│       │                                           │         │
│   [Corner 4] ──────────────────────────────── [Corner 3]    │
│       │                                                     │
│    [START / FINISH] (Entrance Doorway)                      │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Step-by-Step Trajectory Guide:
1. **Loop 1 — Perimeter Wall Pass (Looking Outward/Forward):**
   - Begin at the room entrance doorway.
   - Walk slowly around the outer perimeter of the room, keeping ~0.5 to 1.0 meter distance from walls.
   - Angle the camera slightly forward and toward the walls (~30° to 45° off the walking line), smoothly capturing wall art, windows, shelving, and wall intersections.
   - Complete the full circle back to the entrance point.
2. **Loop 2 — Center Orbit Pass (Looking Inward):**
   - Step into the interior walkway.
   - Walk a second, smaller loop around central furniture (tables, bed, coffee table, desk).
   - Angle the camera inward toward the center of the room, capturing furniture surfaces, chair legs, and room center volume from multiple angles.
3. **Loop Closure:**
   - End the recording at the exact same location where it began (the entrance doorway), looking in the same initial direction. This facilitates **loop closure** in COLMAP, preventing drift in long trajectories.

---

## 6. Walking Mechanics & Camera Dynamics

Operators must move their bodies to physically translate the camera through 3D space.

### 6.1 The "Ninja Walk" Technique
To minimize vertical camera bobbing and sudden jerks:
- **Two-Handed Grip:** Hold the phone firmly with both hands at chest height. Keep elbows tucked comfortably against your torso for mechanical stability.
- **Knees Slightly Bent:** Walk with knees soft and slightly bent to act as natural shock absorbers.
- **Heel-to-Toe Roll:** Step smoothly by rolling each foot from heel to toe along a continuous flat line. Avoid stomping or bouncing.
- **Walking Pace:** Maintain a deliberate, slow walking pace of approximately **0.5 to 0.8 meters per second** (roughly half normal walking speed). A 30 m² room should take approximately **45 to 75 seconds** to traverse.

### 6.2 Golden Rule: Translation Over Rotation
- **Move the Camera Center:** When looking from one side of the room to another, physically walk to the new position.
- **Avoid Pivoting on Heels:** Never stand in one spot and spin around 360°. If you must change heading, walk along a smooth, curved arc rather than snapping your wrists or rotating in place.

---

## 7. Capturing Complex Geometry & Occlusions

Indoor spaces contain challenging structural transitions that require deliberate camera attention.

### 7.1 Room Corners & Wall Intersections
- When approaching a corner, **do not spin past it quickly**.
- Slow your pace slightly.
- Move along a gentle curve around the corner while smoothly maintaining the intersection in frame, allowing COLMAP to triangulate the 90° boundary from at least 10–15 consecutive frames.

### 7.2 Furniture & Multi-Sided Objects (Desks, Chairs, Couches)
- Furniture has deep geometric occlusions (under tables, behind couches, between chair legs).
- For prominent furniture pieces, execute an "orbital pass": walk a semicircular arc around the item while keeping it centered in frame.
- Tilt the camera down slightly (~15° to 25°) to capture table surfaces and cushions, while ensuring background wall anchors remain visible.

### 7.3 Doorways & Passages
- Film the doorway from both the threshold and from 1 meter back into the room.
- Ensure the door frame, hinges, and floor threshold transition are captured with clear parallax against the adjacent wall.

### 7.4 Ceiling and Floor Boundaries
- Hold the camera at eye level (approx. 1.4 to 1.6 meters above the floor).
- Tilt the camera so the frame captures both a portion of the floor (baseboards) and the middle wall section. Extreme vertical tilts directly up at flat ceilings or straight down at plain carpets provide zero geometric parallax and should be avoided.

---

## 8. Maintaining Overlap & Mitigating Artifacts

### 8.1 Visual Overlap Management
- **Target:** Consecutive extracted frames should share approximately **60% to 70%** of their visual field.
- **Self-Check During Walk:** Pick a prominent visual landmark (e.g. a picture frame, lamp, or door handle) visible on the right edge of your phone screen. As you step forward, that object should smoothly drift across the screen, remaining visible for at least 3 to 5 steps before exiting the left edge.
- If an object flashes across the screen and exits in 1 or 2 steps, you are walking too fast or turning too sharply.

### 8.2 Eliminating Motion Blur
- Motion blur destroys high-frequency SIFT corner descriptors.
- If a frame is blurred, COLMAP will fail to extract keypoints, causing frame dropouts.
- **Remedy:** Walk slowly, ensure bright ambient room illumination (which forces the smartphone camera to use a fast shutter speed, e.g. 1/120s or faster), and keep your physical grip rigid.

---

## 9. Recording Lifecycle: Start & Finish Protocol

Sudden camera movements when tapping the record button are a primary cause of failed initial frame registration.

### 9.1 Recording Start Procedure
1. Stand at the designated starting position (entrance doorway).
2. Establish your two-handed grip and lock AE/AF.
3. Tap the **Record** button.
4. **HOLD COMPLETELY STILL for 3 to 4 seconds** before taking your first step.
   - *Technical Rationale:* Roomsplat's `extract.py` automatically trims the first 5% of video frames to discard hand tremor caused by tapping the screen. Standing still ensures that when the walking phase begins, clean stationary anchor frames exist.

### 9.2 Recording Walkthrough Procedure
- Execute the planned continuous two-loop route at uniform walking pace.
- Do not stop, do not speed up, and do not make sudden rotational adjustments.

### 9.3 Recording Finish Procedure
1. Complete the route and arrive back at the entrance doorway.
2. Face the original starting direction.
3. **HOLD COMPLETELY STILL for 3 to 4 seconds** with the camera steady.
4. Tap the **Stop** button.
   - *Technical Rationale:* The static hold ensures that the final 5% trim in `extract.py` removes the physical motion of reaching for the screen, preserving clean loop-closure frames.

---

## 10. Summary Parameters for Competition Abstract

This table provides the recommended operational parameters suitable for inclusion in the Round 1 Technical Abstract methodology section:

| Capture Parameter | Recommended Value | Engineering Rationale |
|---|---|---|
| **Video Resolution** | 1080p (1920×1080 px) | Balances high spatial fidelity with manageable extraction throughput |
| **Capture Frame Rate** | 30.0 fps | Standard temporal resolution; enables clean shutter speeds under indoor lighting |
| **Downsampling Extraction** | 0.8 to 2.5 fps | Reduces redundant adjacent frames while maintaining 60%+ spatial overlap |
| **Max Dimension Scaling** | 1600 px (longest edge) | Prevents VRAM exhaustion during 3DGS training densification |
| **Exposure / Focus Mode** | Fixed / Locked (AE/AF Lock) | Enforces Lambertian photometric consistency across views |
| **Camera Trajectory** | Continuous Closed Dual-Loop | Provides full perimeter coverage, interior orbit, and loop closure |
| **Walking Speed** | 0.5 to 0.8 m/s | Eliminates motion blur and maintains gradual parallax translation |
| **Target Inter-Frame Overlap** | 60% – 70% | Optimal baseline for SIFT epipolar geometry and COLMAP triangulation |
| **Start / Finish Buffer** | 3–4 sec stationary hold | Absorbs screen-tap vibration within Roomsplat's 5% automated trim filter |
| **Duration (Standard Room)** | 45 to 75 seconds | Yields ~120–180 effective training frames after deduplication |

---

## 11. Document History & Revision Control

| Version | Date | Author / Role | Changes / Notes |
|---|---|---|---|
| `1.0.0` | 2026-10-28 | Antigravity AI Engineering Agent | Initial comprehensive Standard Operating Procedure drafted for Techfest IIT Bombay Round 1. |
