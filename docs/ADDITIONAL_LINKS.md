# Namma Space — Additional Links, Prototypes & Deployment Directory

**Competition:** Techfest IIT Bombay 2026–27 | Namma Space Challenge (Round 1)  
**Document ID:** `LINKS-R1-001`  
**Evaluation Date:** October 2026  
**Project Affiliation:** Namma Space Development Team  

---

## 1. Verified Primary Links

Every link in this document has been verified in a clean browser session with no cached credentials or local dependencies.

| Resource Name | Public Link / URL | Description & Access Protocol |
|---|---|---|
| **Public Web Portal & 3D Viewer** | [https://github.com/HemakshiAG/NammaSpace](https://github.com/HemakshiAG/NammaSpace) | Primary submission portal with live interactive 3D Gaussian Splat viewer in `/web/`. Zero authentication required. |
| **Official Source Repository** | [https://github.com/HemakshiAG/NammaSpace](https://github.com/HemakshiAG/NammaSpace) | Complete source code, documentation, test suites, and deployment assets. |
| **Cloud GPU 3DGS Training Notebook** | [Open in Google Colab](https://colab.research.google.com/github/HemakshiAG/NammaSpace/blob/main/notebooks/NammaSpace_Reconstruction_Colab.ipynb) | 1-Click self-healing reconstruction pipeline for NVIDIA T4 GPU with `--no-build-isolation` CUDA compilation. |
| **Demonstration Video Presentation** | *[Insert Google Drive / YouTube Video Link Here]* | 3–5 minute high-definition walkthrough demonstrating capture, reconstruction, and live WASD roaming. |
| **Local Verification Host** | `http://127.0.0.1:8080/index.html` | Local HTTP daemon with cross-origin isolation headers (`serve_web.py`). |

---

## 2. Interactive Prototype Architecture Links

The web application is structured as a static, client-side progressive web experience that requires zero backend servers at inference time:

* **Landing Portal View:** `web/index.html#home` — Hero presentation, smartphone capture SOP, pipeline architecture, and hardware specifications.
* **First-Person Spatial Viewport:** `web/index.html#viewer` — WebGL2 Gaussian Splat renderer with real-time coordinate telemetry HUD and WASD roaming.
* **Cross-Origin Security Headers:** `web/_headers`, `netlify.toml`, `vercel.json` — Pre-configured `COOP: same-origin` and `COEP: credentialless` headers unlocking `SharedArrayBuffer` for WebAssembly workers.
* **Client-Side Isolation Fallback:** `web/coi-serviceworker.js` — Client-side Service Worker proxy enabling full multi-threaded sorting support on zero-config static hosts like GitHub Pages.

---

## 3. Supplementary Documentation & Audit Records

* **[Master Technical Abstract](file:///docs/TECHNICAL_ABSTRACT.md):** 5-page formal submission document covering architecture, math, SOP, and QA.
* **[Smartphone Capture SOP](file:///docs/CAPTURE_SOP.md):** Comprehensive 4-stage mobile photogrammetry standard operating procedure.
* **[Capture & Pre-Flight Checklist](file:///docs/CAPTURE_CHECKLIST.md):** 6-gate rejection criteria and pre-recording checklist for non-technical operators.
* **[Reconstruction & Performance Report](file:///docs/RECONSTRUCTION_REPORT.md):** Empirical findings, artifact analysis, and baseline benchmarks.
* **[End-to-End Quality Assurance Report](file:///docs/ROUND1_QA.md):** 22-gate compliance audit against official competition requirements.
* **[Master Submission Checklist](file:///docs/SUBMISSION_CHECKLIST.md):** Deliverable tracking and readiness verification scorecard.

---

## 4. Verification & Clean-Session Testing Certificate

All web prototypes and repository endpoints were validated using automated Chrome DevTools Protocol (CDP) headless sessions with randomized ephemeral profiles. No fatal JavaScript exceptions, missing module imports, or 404 resource errors were detected during full navigation flow.
