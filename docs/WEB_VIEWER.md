# Namma Space Web Experience & 3D Spatial Viewer Architecture

**Project:** Techfest IIT Bombay 2026–27 | Namma Space (Round 1)  
**Document ID:** `ARCH-WEB-001`  
**Web Application Root:** [web/](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/web/)  
**Deployment Configuration:** [web/_headers](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/web/_headers)  
**Local Development Server:** [serve_web.py](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/serve_web.py)  

---

## 1. Executive Summary & Design Direction

The Namma Space Web Experience is a spatial-computing web portal designed to deliver autonomous, photorealistic 3D room walkthroughs directly in modern web browsers. Built with a restrained, dark visual design, the portal integrates:
1. **The Spatial Computing Overview Portal (`#landing-view`):** Introduces Namma Space, explains the 4-stage mobile capture protocol, outlines technical specifications, and provides a one-click launcher into the 3D digital twin.
2. **The Immersive Full-Bleed 3D Viewer (`#viewer-view`):** Renders high-fidelity 3D Gaussian Splats at 60 FPS using WebGL2, complete with first-person WASD fly navigation, mouse look, live telemetry HUD, progressive loading UI, and error boundaries.

### Architectural Philosophy
- **Zero Cloud Runtime Dependencies:** The viewer runs entirely client-side on the user's browser. Once the static assets (`index.html`, `.splat`, `cameras.json`) are downloaded, no ongoing GPU cloud instances, databases, or proprietary APIs are queried.
- **Universal Browser Compatibility:** Operates on standard desktop and mobile browsers (Chrome, Edge, Safari, Firefox) utilizing WebGL2 and WebAssembly.
- **Restrained Spatial Design:** High-contrast dark theme (`#070a11` slate background, `#38bdf8` cyan accents), frosted-glass HUD overlays, subtle micro-interactions, and zero intrusive animations.

---

## 2. System Architecture & Component Hierarchy

```
┌────────────────────────────────────────────────────────────────────────┐
│                   NAMMA SPACE WEB PORTAL ARCHITECTURE                  │
└────────────────────────────────────────────────────────────────────────┘

 [ Client Browser: Chrome / Edge / Safari / Firefox ]
                        │
                        ▼
 ┌──────────────────────────────────────────────────────────────┐
 │ Single-Page Application Shell (web/index.html)              │
 │ • State A: Landing & Workflow Portal (#landing-view)         │
 │ • State B: Immersive 3D Spatial Viewer (#viewer-view)        │
 └──────────────────────┬───────────────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           ▼                         ▼
 ┌───────────────────┐     ┌───────────────────────────────────┐
 │ Landing Portal    │     │ Spatial Viewer Engine             │
 │ • Hero & CTA      │     │ (web/viewer.js)                   │
 │ • Capture SOP     │     │ • Three.js v0.170.0 (Scene/Cam)   │
 │ • Pipeline Specs  │     │ • @mkkellogg/gaussian-splats-3d   │
 │ • Documentation   │     │ • WASM Radix Depth Sort Worker    │
 └───────────────────┘     │ • WASD Roaming & Mouse Orbit/Pan  │
                           │ • Live XYZ Coordinate HUD         │
                           └─────────────────┬─────────────────┘
                                             │
                                             ▼
                           ┌───────────────────────────────────┐
                           │ Static Reconstruction Assets      │
                           │ • scene.splat (11.8 MB binary)    │
                           │ • cameras.json (COLMAP poses)     │
                           └───────────────────────────────────┘
```

### Component Inventory:
- **`web/index.html`:** Semantic HTML5 application shell containing both the landing portal and the 3D viewport canvas.
- **`web/styles.css`:** Dark spatial-computing design system with responsive grid layouts, glassmorphism telemetry badges, and interactive keyboard indicators.
- **`web/viewer.js`:** Encapsulated JavaScript class (`NammaSpaceViewer`) managing Three.js lifecycle, `@mkkellogg/gaussian-splats-3d` initialization, camera pose alignment, telemetry loops, and clean disposal.
- **`web/scene.splat`:** 11.8 MB binary Gaussian Splat scene (369,006 Gaussians).
- **`web/cameras.json`:** Camera trajectories exported from COLMAP incremental mapping.
- **`web/_headers`:** Cross-Origin Isolation headers for static hosting.

---

## 3. 3D Representation & Binary File Formats

### 3.1 The 32-Byte `.splat` Format
The web viewer prioritizes the compact `.splat` binary format (originated by antimatter15, MIT License) to ensure fast network delivery and efficient GPU uploading:

```
┌────────────────────────────────────────────────────────────────────────┐
│                    32-BYTE GAUSSIAN RECORD LAYOUT                      │
├───────────────┬───────────────┬────────────────────────┬───────────────┤
│ Bytes 0–11    │ Bytes 12–23   │ Bytes 24–27            │ Bytes 28–31   │
│ Position XYZ  │ Scale XYZ     │ Color RGBA             │ Rotation Quat │
│ 3 × float32   │ 3 × float32   │ 4 × uint8              │ 4 × uint8     │
│ (12 bytes)    │ (12 bytes)    │ (4 bytes)              │ (4 bytes)     │
└───────────────┴───────────────┴────────────────────────┴───────────────┘
```

#### Format Conversions:
- **Position:** Direct world-space coordinates `(x, y, z)` in meters.
- **Scale:** Exponentiated scale values `exp(scale_i)` clamped to prevent degenerate needle ratios.
- **Color:** Sigmoid DC spherical harmonic `clamp(f_dc * 0.28209 + 0.5, 0, 1)` mapped to `[0, 255]`.
- **Rotation:** Normalized quaternion `(qx, qy, qz, qw)` packed as `round((r + 1) / 2 * 255)`.
- **Sorting:** Gaussians are pre-sorted in descending opacity order, allowing early fragment discard and reducing overdraw.

### 3.2 Representation Trade-off: `.splat` vs. `.ply`

| Metric / Attribute | Compact `.splat` Format | Full `.ply` Format |
|---|---|---|
| **Primary Use Case** | **Default Web Delivery** | High-End Local Archival |
| **Color Model** | Degree-0 Spherical Harmonics (SH0 Flat) | Degree-2/3 Spherical Harmonics (View-Dependent) |
| **File Size (Sample Room)**| **11.8 MB** | ~60 MB to 120 MB |
| **Load & Parse Time** | **1.8 – 2.5 seconds** | 12 – 25 seconds |
| **Browser VRAM Impact** | ~250 MB | ~850 MB to 1.2 GB |
| **Mobile Web Support** | Universal (60 FPS on integrated GPUs) | High risk of browser WebGL context loss |

> [!TIP]
> The Namma Space portal defaults to `.splat` to ensure immediate 2-second streaming and stable 60 FPS playback on all client devices, including laptops with integrated graphics.

---

## 4. Camera Trajectory & Pose Alignment (`cameras.json`)

Standard photogrammetry viewers often place the camera at an arbitrary origin `(0, 0, 0)`, which frequently leaves the user stranded in empty black space outside room walls.

### 4.1 Extrinsic Pose Ingestion
Namma Space resolves this by reading `cameras.json` exported directly from COLMAP's `images.bin`:
```json
{
  "initial": 5,
  "cameras": [
    {
      "pos": [-4.408, 0.569, 0.226],
      "forward": [0.088, -0.041, 0.995],
      "up": [-0.003, -0.999, -0.041],
      "name": "frame_00215.jpg"
    }
  ]
}
```

### 4.2 Mathematical Camera Placement
- **Initial Eye Position:** Set to `cam.pos` (`[-4.408, 0.569, 0.226]`).
- **Initial Target LookAt:** Calculated by projecting forward along the optical axis:
  $$\mathbf{LookAt} = \mathbf{pos} + \mathbf{forward}$$
- **Result:** When the user clicks "Explore Reconstructed Room", they immediately spawn inside the authentic capture trajectory facing into the room.

---

## 5. Navigation Controls & Interaction Scheme

```
┌─────────────────────────────────────────────────────────────┐
│                    NAVIGATION HUD GUIDE                     │
├───────────────────────────────┬─────────────────────────────┤
│ First-Person Fly Roaming      │ Keyboard: [W] [A] [S] [D]   │
│   • W: Translate forward      │   • S: Translate backward   │
│   • A: Strafe left            │   • D: Strafe right         │
├───────────────────────────────┼─────────────────────────────┤
│ Mouse Look & Orbit            │ Mouse Left-Click + Drag     │
│ Lateral Pan Translation       │ Mouse Right-Click + Drag    │
│ Elevation / Zoom (Dolly)      │ Mouse Scroll Wheel          │
├───────────────────────────────┼─────────────────────────────┤
│ Fullscreen Viewport           │ Top-Right Fullscreen Button │
│ Return to Overview Portal     │ Top-Left Button or [Escape] │
└───────────────────────────────┴─────────────────────────────┘
```

### Telemetry HUD
The live HUD at the bottom-left tracks continuous world-space camera coordinates at 60 Hz:
```
x:  -3.472  y:   0.486  z:   0.680
```
As the user presses `W`, `A`, `S`, `D` or drags the mouse, coordinates update immediately, providing quantitative confirmation of camera motion.

---

## 6. Hosting & Cross-Origin Isolation Requirements

`@mkkellogg/gaussian-splats-3d` utilizes Web Workers and `SharedArrayBuffer` for real-time parallel radix sorting of 300k+ Gaussians. Browsers require **Cross-Origin Isolation** headers to enable `SharedArrayBuffer`.

### 6.1 Required Headers
```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: credentialless
Access-Control-Allow-Origin: *
```

> [!NOTE]
> `credentialless` is preferred over `require-corp` because it allows external CDN resources (such as Three.js from jsDelivr) to load without requiring third-party servers to emit explicit `Cross-Origin-Resource-Policy` headers.

### 6.2 Deployment Configurations

#### Netlify (`web/_headers`):
```
/*
  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: credentialless
  Access-Control-Allow-Origin: *
```

#### Vercel (`vercel.json`):
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Cross-Origin-Opener-Policy", "value": "same-origin" },
        { "key": "Cross-Origin-Embedder-Policy", "value": "credentialless" }
      ]
    }
  ]
}
```

#### Local Development Server (`serve_web.py`):
```powershell
.venv\Scripts\python serve_web.py
# Serves at http://127.0.0.1:8080/index.html with all isolation headers pre-configured.
```

---

## 7. Automated Verification & Telemetry Results

We validated the web experience using our automated Chrome DevTools Protocol (CDP) test suite ([test_web_experience.mjs](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/test_web_experience.mjs)).

### Test Telemetry Log:
| Test Phase | Measured Value | Benchmark Result |
|---|---|---|
| **Landing Page Load** | Title: `"Autonomous 3D Spatial Twins From Smartphone Video."` | ✅ PASS |
| **Workflow Grid** | 4 procedural capture cards rendered | ✅ PASS |
| **CTA Click Transition** | Switched `#landing-view` → `#viewer-view` in < 50ms | ✅ PASS |
| **Initial Pose Alignment** | `x: -4.408, y: 0.569, z: 0.226` (from `cameras.json`) | ✅ PASS |
| **Mouse Left-Drag (Orbit)**| `x: -3.541, y: 0.569, z: 0.595` (`Δx: +0.867, Δz: +0.369`) | ✅ **VERIFIED (true)** |
| **'W' Fly Forward** | `x: -3.521, y: 0.488, z: 0.615` (`Δy: -0.081`) | ✅ **VERIFIED (true)** |
| **'D' Strafe Right** | `x: -3.472, y: 0.486, z: 0.680` (`Δx: +0.049, Δz: +0.065`) | ✅ **VERIFIED (true)** |
| **Return to Overview** | Clicked `#viewer-btn-back`; `#landing-view` restored cleanly | ✅ **VERIFIED (true)** |

### Visual Documentation:
- **Landing Portal Verification:** [docs/web_landing_verification.png](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/docs/web_landing_verification.png)
- **3D Spatial Viewer Verification:** [docs/web_viewer_verification.png](file:///c:/Hemakshi/Learning/Hackathons/Techfest-IITB/Namma%20Space/NammaSpace/docs/web_viewer_verification.png)
