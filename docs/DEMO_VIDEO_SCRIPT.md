# Namma Space — Demonstration Video Presentation Script & Recording Guide

**Competition:** Techfest IIT Bombay 2026–27 | Namma Space Challenge (Round 1)  
**Target Duration:** 3 minutes 30 seconds to 4 minutes 45 seconds (Target: ~4:15)  
**Audio Format:** Clear voiceover / narration  
**Video Format:** 1080p @ 60 fps (Full screen web browser + camera walkthrough clips)  
**Recording Tool:** OBS Studio, Loom, or Windows Game Bar (`Win + Alt + R`)  

---

## 🎬 Timestamped Narration & Visual Director Cue Card

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DEMO VIDEO TIMELINE OVERVIEW                              │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [0:00 - 0:25]  Introduction & Real Estate Problem Statement
 [0:25 - 1:00]  Smartphone Capture SOP & Authentic Room Walkthrough
 [1:00 - 1:45]  Reconstruction Pipeline & Genuine COLMAP/3DGS Execution Evidence
 [1:45 - 3:30]  Live Web Viewer Roaming Demo (WASD Fly, Mouse Orbit & Telemetry HUD)
 [3:30 - 4:15]  Architectural Details, 32-Byte Splat Format & WebAssembly Sorting
 [4:15 - 4:45]  Honest Limitations, Hardware Boundaries & Future Round 2 Roadmap
```

---

### [0:00 – 0:25] Act I: Introduction & The Problem
* **On Screen:** Namma Space web portal landing page ([https://github.com/HemakshiAG/NammaSpace](https://github.com/HemakshiAG/NammaSpace)). Clean title view showing "Autonomous 3D Spatial Twins From Smartphone Video".
* **Presenter Voiceover:**  
  *"Hello judges. Welcome to Namma Space, our submission for Techfest IIT Bombay's Namma Space Challenge Round 1.  
  Today, exploring real estate remotely is broken. Users are either forced to jump through clunky 360-degree photo bubbles that distort scale and break immersion, or companies have to deploy expensive, multi-thousand-dollar LiDAR equipment.  
  Namma Space solves this by turning ordinary, continuous smartphone walkthrough videos into photorealistic, continuous 3D radiance fields that anyone can freely roam inside any standard web browser with zero installation."*

---

### [0:25 – 1:00] Act II: Smartphone Capture SOP & The Room
* **On Screen:** Split screen or transition showing:
  1. The recorded video clip (`test_vid1.mp4` / `my_room.mp4`) being filmed on a phone.
  2. The 4-Stage Capture Protocol section on the Namma Space landing page.
* **Presenter Voiceover:**  
  *"Photogrammetry fails when video is filmed casually without sufficient baseline parallax. To guarantee high-quality reconstructions, we established a strict 4-stage Capture Standard Operating Procedure.  
  First, room conditioning: diffuse lighting, stationary furniture, and high-contrast markers on featureless walls.  
  Second, sensor configuration: 1080p at 30 fps in landscape with standard 1.0x optical lens, and critically, Auto-Exposure and Auto-Focus locked to preserve photometric consistency.  
  Third, our dual-loop trajectory: a 45-to-75 second heel-to-toe 'ninja walk'. The operator completes an outer perimeter pass facing walls and corners, followed by a tight inward-facing orbit around central furniture.  
  Finally, stationary 3-second buffers at the start and end to eliminate screen-tap vibration."*

---

### [1:00 – 1:45] Act III: The Reconstruction Pipeline & Processing Evidence
* **On Screen:** Show the Google Colab / terminal execution logs showing PyColmap and 3D Gaussian Splatting training:
  - FFMPEG frame extraction output (`✓ 94 frames -> ...`)
  - PyColmap pose estimation matching graph and registered cameras
  - 3DGS training progress (`Iteration 7000... 30000`)
* **Presenter Voiceover:**  
  *"Our reconstruction engine processes this video in four rigorous steps.  
  First, FFMPEG temporally subsamples the video at 1.5 frames per second, selecting sharp, unblurred frames while eliminating redundant data.  
  Next, PyColmap executes Structure-from-Motion, extracting SIFT features and computing 6-DoF camera trajectories and intrinsic calibration.  
  Then, Inria 3D Gaussian Splatting optimizes over 300,000 volumetric 3D Gaussians across 30,000 iterations on an NVIDIA GPU, modeling complex view-dependent specular reflections via spherical harmonics.  
  Finally, the dense model is compressed into a 32-byte-per-splat binary `.splat` file of just 11.8 MB, accompanied by camera initialization vectors in `cameras.json`."*

---

### [1:45 – 3:30] Act IV: Live Web Viewer & First-Person Roaming
* **On Screen:** Click **"Explore Reconstructed Room"** on the web portal. The screen transitions into the 3D WebGL2 viewer.
  - Show the scene streaming and loading smoothly.
  - Perform live first-person navigation using `W`, `A`, `S`, `D` keys.
  - Show the floating Telemetry HUD: point out real-time `x, y, z` coordinates changing smoothly.
  - Show mouse left-click orbit and right-click panning around desks, chairs, monitors, and corners.
  - Highlight the active WASD visual badges lighting up green during keypresses.
* **Presenter Voiceover:**  
  *"Now let's launch the live web viewer. Notice that this opens instantly inside Google Chrome without requiring any plugins, login credentials, or downloads.  
  The 11.8 MB scene streams in under 2 seconds. The camera initializes at a genuine registered camera pose extracted from COLMAP, placing us right at the room entrance.  
  Using WASD, we can freely fly through the room. As I press 'W', you can see our camera coordinates updating in real-time on our live glassmorphic telemetry HUD. Pressing 'A' and 'D' executes horizontal strafing.  
  With mouse drag, we can orbit our look-vector smoothly around desks, monitors, and chairs. Notice the sharp text on screens and realistic specular highlights on metallic surfaces.  
  The rendering maintains a rock-solid 60 FPS on standard integrated consumer GPUs, thanks to a dedicated WebAssembly worker running radix depth sorting off the main browser thread."*

---

### [3:30 – 4:15] Act V: Technical Choices & Architecture
* **On Screen:** Show the web codebase architecture (`web/index.html`, `web/viewer.js`, `web/_headers`), and the GitHub repository.
* **Presenter Voiceover:**  
  *"Our technical design focuses on extreme client-side efficiency. Instead of heavy JavaScript frameworks, we built a zero-dependency static web application using vanilla HTML5, CSS custom tokens, and ES Modules.  
  To solve the major security barrier of running WebAssembly multi-threaded sorting in browsers, we configured Cross-Origin Isolation headers (`COOP` and `COEP`) with a client-side service worker fallback. This enables `SharedArrayBuffer` support on any static hosting environment, including GitHub Pages and Netlify.  
  The complete deployable bundle is under 12 MB, loading in less than two seconds."*

---

### [4:15 – 4:45] Act VI: Honest Limitations & Conclusion
* **On Screen:** Show the Documentation and QA report (`docs/ROUND1_QA.md`), then return to the landing portal.
* **Presenter Voiceover:**  
  *"In compliance with competition guidelines, we transparently state our current limitations. High-iteration 3D Gaussian Splatting requires NVIDIA CUDA hardware, which we handle via cloud GPUs. Specular reflections on large mirrors can introduce floating artifacts, which our dual-loop capture helps mitigate.  
  In Round 2, we plan to implement 3D semantic segmentation for Point-of-Interest search and NavMesh collision boundaries for walking constraints.  
  Namma Space proves that high-fidelity indoor digital twins can be captured from an everyday smartphone and experienced anywhere on the web. Thank you!"*

---

## 🎙️ Recording Checklist
- [ ] Set browser window to 1080p (`1920x1080`) or full-screen.
- [ ] Close unnecessary background tabs to ensure steady 60 FPS recording.
- [ ] Ensure microphone audio has zero echo and balanced volume.
- [ ] Verify that mouse cursor is visible during screen recording.
- [ ] Save output as `Demo_Video.mp4` (H.264 video codec, AAC audio).
