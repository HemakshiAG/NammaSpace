# Comprehensive System & Deliverable Readiness Auditor
import json
import os
import re
import urllib.request
from pathlib import Path

WORKSPACE = Path(__file__).parent.resolve()

def check_file(path: Path, min_bytes: int = 1) -> tuple[bool, str]:
    if not path.exists():
        return False, f"MISSING: {path.relative_to(WORKSPACE)}"
    size = path.stat().st_size
    if size < min_bytes:
        return False, f"TOO SMALL ({size} bytes < {min_bytes}): {path.relative_to(WORKSPACE)}"
    return True, f"OK ({size:,} bytes): {path.relative_to(WORKSPACE)}"

def count_pdf_pages(pdf_path: Path) -> int:
    with open(pdf_path, 'rb') as f:
        content = f.read().decode('latin1', errors='ignore')
    return len(re.findall(r'/Type\s*/Page\b', content))

def audit():
    print("=" * 80)
    print("      NAMMA SPACE — TECHFEST IIT BOMBAY ROUND 1 COMPLIANCE AUDIT")
    print("=" * 80)
    
    failures = 0
    total_checks = 0

    # 1. Root & Core Config Files
    print("\n--- 1. ROOT REPOSITORY FILES ---")
    core_files = [
        WORKSPACE / "README.md",
        WORKSPACE / "index.html",
        WORKSPACE / "netlify.toml",
        WORKSPACE / "vercel.json",
        WORKSPACE / "serve_web.py",
        WORKSPACE / "build_submission_bundle.py",
        WORKSPACE / "test_web_experience.mjs",
    ]
    for f in core_files:
        total_checks += 1
        ok, msg = check_file(f, min_bytes=50)
        print(f"[{'PASS' if ok else 'FAIL'}] {msg}")
        if not ok: failures += 1

    # 2. Web Deployment Bundle (/web/)
    print("\n--- 2. WEB APPLICATION BUNDLE (/web/) ---")
    web_files = [
        (WORKSPACE / "web" / "index.html", 5000),
        (WORKSPACE / "web" / "styles.css", 4000),
        (WORKSPACE / "web" / "viewer.js", 3000),
        (WORKSPACE / "web" / "coi-serviceworker.js", 1000),
        (WORKSPACE / "web" / "scene.splat", 5_000_000),
        (WORKSPACE / "web" / "cameras.json", 100),
        (WORKSPACE / "web" / "_headers", 50),
    ]
    for f, min_b in web_files:
        total_checks += 1
        ok, msg = check_file(f, min_bytes=min_b)
        print(f"[{'PASS' if ok else 'FAIL'}] {msg}")
        if not ok: failures += 1

    # 3. Documentation Directory (/docs/)
    print("\n--- 3. DOCUMENTATION DIRECTORY (/docs/) ---")
    doc_files = [
        "TECHNICAL_ABSTRACT.md",
        "ADDITIONAL_LINKS.md",
        "SUBMISSION_CHECKLIST.md",
        "CAPTURE_SOP.md",
        "CAPTURE_CHECKLIST.md",
        "ENVIRONMENT_AUDIT.md",
        "REPOSITORY_AUDIT.md",
        "PIPELINE_SETUP.md",
        "RECONSTRUCTION_REPORT.md",
        "WEB_VIEWER.md",
        "DEPLOYMENT.md",
        "ROUND1_QA.md",
        "DEMO_VIDEO_SCRIPT.md",
        "web_landing_verification.png",
        "web_viewer_verification.png",
        "viewer_roaming_verification.png",
    ]
    for name in doc_files:
        total_checks += 1
        ok, msg = check_file(WORKSPACE / "docs" / name, min_bytes=100)
        print(f"[{'PASS' if ok else 'FAIL'}] {msg}")
        if not ok: failures += 1

    # 4. Google Drive Submission Bundle (/submission_bundle/NammaSpace_Round1/)
    print("\n--- 4. GOOGLE DRIVE SUBMISSION BUNDLE (NammaSpace_Round1) ---")
    bundle_root = WORKSPACE / "submission_bundle" / "NammaSpace_Round1"
    bundle_files = [
        (bundle_root / "Technical_Abstract.pdf", 5000),
        (bundle_root / "Additional_Links_and_Prototypes.pdf", 2000),
        (bundle_root / "Repository_README.pdf", 2000),
        (bundle_root / "Demo_Video_README.txt", 100),
        (bundle_root / "Screenshots" / "web_landing_portal.png", 50_000),
        (bundle_root / "Screenshots" / "web_viewer_roaming.png", 50_000),
        (bundle_root / "Screenshots" / "viewer_wasd_telemetry.png", 50_000),
        (bundle_root / "Sample_Data" / "sample_synthetic_walkthrough.mp4", 1_000_000),
        (bundle_root / "Sample_Data" / "README.md", 200),
    ]
    for f, min_b in bundle_files:
        total_checks += 1
        ok, msg = check_file(f, min_bytes=min_b)
        print(f"[{'PASS' if ok else 'FAIL'}] {msg}")
        if not ok: failures += 1

    # 5. PDF Page Count Verification
    print("\n--- 5. PDF PAGE CEILING VERIFICATION ---")
    tech_abs = bundle_root / "Technical_Abstract.pdf"
    if tech_abs.exists():
        total_checks += 1
        pages = count_pdf_pages(tech_abs)
        ok = (1 <= pages <= 5)
        print(f"[{'PASS' if ok else 'FAIL'}] Technical_Abstract.pdf Page Count: {pages} pages (Limit: <= 5 pages)")
        if not ok: failures += 1

    # 6. Notebook JSON Validation
    print("\n--- 6. GOOGLE COLAB RECONSTRUCTION NOTEBOOK ---")
    nb_file = WORKSPACE / "notebooks" / "NammaSpace_Reconstruction_Colab.ipynb"
    total_checks += 1
    if nb_file.exists():
        try:
            with open(nb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cells = len(data.get("cells", []))
            print(f"[PASS] Valid Jupyter Notebook format ({cells} cells): {nb_file.relative_to(WORKSPACE)}")
        except Exception as e:
            print(f"[FAIL] Invalid JSON in notebook: {e}")
            failures += 1
    else:
        print(f"[FAIL] Missing notebook: {nb_file}")
        failures += 1

    # 7. Local HTTP Server & Isolation Headers Test
    print("\n--- 7. LIVE HTTP SERVER & HEADERS AUDIT (http://127.0.0.1:8080) ---")
    server_urls = [
        "http://127.0.0.1:8080/index.html",
        "http://127.0.0.1:8080/styles.css",
        "http://127.0.0.1:8080/viewer.js",
        "http://127.0.0.1:8080/coi-serviceworker.js",
        "http://127.0.0.1:8080/cameras.json",
        "http://127.0.0.1:8080/scene.splat",
    ]
    server_online = True
    for url in server_urls:
        total_checks += 1
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=3) as resp:
                status = resp.status
                coop = resp.headers.get("Cross-Origin-Opener-Policy", "")
                coep = resp.headers.get("Cross-Origin-Embedder-Policy", "")
                ok = (status == 200)
                print(f"[{'PASS' if ok else 'FAIL'}] HTTP {status}: {url} (COOP: '{coop}', COEP: '{coep}')")
                if not ok: failures += 1
        except Exception as e:
            server_online = False
            print(f"[WARN] Local server fetch failed for {url}: {e}")
            failures += 1

    # Final Summary
    print("\n" + "=" * 80)
    passed_checks = total_checks - failures
    pct = (passed_checks / total_checks) * 100
    print(f"AUDIT SUMMARY: {passed_checks}/{total_checks} Checks Passed ({pct:.1f}%) | {failures} Failures")
    if failures == 0:
        print("ALL AUDITED COMPONENTS, FILES, PDFS, AND LIVE ENDPOINTS ARE IN PLACE AND VERIFIED!")
    else:
        print(f"ATTENTION: {failures} checks did not pass. Review the detailed log above.")
    print("=" * 80)

if __name__ == "__main__":
    audit()
