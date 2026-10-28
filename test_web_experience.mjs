// End-to-End Automated Validation of Namma Space Web Experience via Native CDP
import { writeFileSync } from 'fs';
import { spawn } from 'child_process';
import { resolve } from 'path';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PROFILE_DIR = resolve(process.env.TEMP || "C:\\temp", `chrome_cdp_web_${Date.now()}`);
const TARGET_URL = "http://127.0.0.1:8080/index.html";

console.log("=== Starting End-to-End Validation of Namma Space Web Experience ===");

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9224",
  `--user-data-dir=${PROFILE_DIR}`,
  "--headless=new",
  "--use-gl=angle",
  "--use-angle=d3d11",
  "--window-size=1280,720",
  TARGET_URL
]);

chromeProc.on('error', (err) => {
  console.error("Failed to spawn Chrome:", err);
  process.exit(1);
});

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function runTest() {
  let wsUrl = null;
  for (let i = 0; i < 30; i++) {
    await sleep(500);
    try {
      const res = await fetch("http://127.0.0.1:9224/json");
      if (res.ok) {
        const pages = await res.json();
        const page = pages.find(p => p.type === 'page');
        if (page && page.webSocketDebuggerUrl) {
          wsUrl = page.webSocketDebuggerUrl;
          console.log("Connected to Chrome target:", page.title, page.url);
          break;
        }
      }
    } catch (_) {}
  }

  if (!wsUrl) {
    console.error("Could not find WebSocket debugger URL on port 9224");
    chromeProc.kill();
    process.exit(1);
  }

  const ws = new WebSocket(wsUrl);
  let id = 1;
  const callbacks = new Map();

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.method === 'Runtime.consoleAPICalled') {
      const text = msg.params.args.map(a => a.value ?? a.description ?? JSON.stringify(a)).join(' ');
      console.log(`[Browser Console] ${text}`);
    }
    if (msg.id && callbacks.has(msg.id)) {
      callbacks.get(msg.id)(msg);
      callbacks.delete(msg.id);
    }
  };

  const send = (method, params = {}) => new Promise((resolve) => {
    const msgId = id++;
    callbacks.set(msgId, resolve);
    ws.send(JSON.stringify({ id: msgId, method, params }));
  });

  await new Promise(r => ws.onopen = r);
  console.log("WebSocket connection established to Chrome DevTools.");

  await send("Page.enable");
  await send("Runtime.enable");

  const evalExpr = async (expr) => {
    const res = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
    return res.result?.result?.value;
  };

  // Explicitly navigate to ensure clean state
  console.log(`Navigating directly to ${TARGET_URL}...`);
  await send("Page.navigate", { url: TARGET_URL });

  // Wait for document readyState complete
  for (let i = 0; i < 20; i++) {
    await sleep(500);
    const readyState = await evalExpr("document.readyState");
    if (readyState === 'complete') break;
  }

  // ── 1. Validate Landing Page ────────────────────────────────────────────────
  console.log("\n--- Validating Landing Page Elements ---");
  await sleep(1000);
  const heroTitle = await evalExpr("document.querySelector('.hero-title')?.innerText");
  const landingHidden = await evalExpr("document.getElementById('landing-view')?.classList.contains('view-hidden')");
  const workflowCardCount = await evalExpr("document.querySelectorAll('#workflow .card')?.length");

  console.log(`Hero Title: "${heroTitle?.replace(/\n/g, ' ')}"`);
  console.log(`Landing Visible: ${!landingHidden}`);
  console.log(`Workflow Cards Found: ${workflowCardCount}`);

  // Screenshot Landing Page
  const landingScreenshot = await send("Page.captureScreenshot", { format: "png" });
  if (landingScreenshot.result?.data) {
    const buf = Buffer.from(landingScreenshot.result.data, 'base64');
    const path = resolve("docs", "web_landing_verification.png");
    writeFileSync(path, buf);
    console.log(`Landing screenshot saved: ${path} (${buf.length} bytes)`);
  }

  // ── 2. Trigger "Explore Reconstructed Room" ────────────────────────────────
  console.log("\n--- Clicking 'Explore Reconstructed Room' CTA Button ---");
  await evalExpr("document.getElementById('hero-btn-launch').click()");
  await sleep(1000);

  const viewerHidden = await evalExpr("document.getElementById('viewer-view')?.classList.contains('view-hidden')");
  console.log(`Viewer View Active: ${!viewerHidden}`);

  // ── 3. Wait for 3D Gaussian Scene to Load ──────────────────────────────────
  console.log("\n--- Waiting for 3D Splat Scene Stream & Shader Compilation ---");
  let loaded = false;
  for (let i = 0; i < 45; i++) {
    await sleep(1000);
    const loadingDisplay = await evalExpr("document.getElementById('viewer-loading')?.style.display");
    const statusText = await evalExpr("document.getElementById('loading-status-detail')?.innerText");
    const coords = await evalExpr("document.getElementById('viewer-coords')?.innerText");

    if (i % 5 === 0 || loadingDisplay === 'none') {
      console.log(`[${i}s] Status: "${statusText}" | Loading Display: "${loadingDisplay}" | Coords: "${coords}"`);
    }

    if (loadingDisplay === 'none' && coords && coords.includes('x:')) {
      loaded = true;
      break;
    }
  }

  const initialCoords = await evalExpr("document.getElementById('viewer-coords')?.innerText");
  console.log(`Initial Reconstructed Room Coords: "${initialCoords}"`);

  // ── 4. Test Mouse Orbit ─────────────────────────────────────────────────────
  console.log("\n--- Testing Mouse Left-Drag Orbit ---");
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: 640, y: 360, button: "left", clickCount: 1 });
  for (let x = 640; x >= 440; x -= 20) {
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x, y: 360, button: "left" });
    await sleep(30);
  }
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: 440, y: 360, button: "left" });
  await sleep(800);

  const postMouseCoords = await evalExpr("document.getElementById('viewer-coords')?.innerText");
  console.log(`Post-Mouse Orbit Coords: "${postMouseCoords}"`);

  // ── 5. Test WASD Fly Navigation ─────────────────────────────────────────────
  console.log("\n--- Testing 'W' (Fly Forward) & 'D' (Strafe Right) ---");
  for (let step = 0; step < 8; step++) {
    await send("Input.dispatchKeyEvent", { type: "rawKeyDown", windowsVirtualKeyCode: 87, code: "KeyW", key: "w" });
    await sleep(80);
    await send("Input.dispatchKeyEvent", { type: "keyUp", windowsVirtualKeyCode: 87, code: "KeyW", key: "w" });
    await sleep(40);
  }
  await sleep(600);

  const postWCoords = await evalExpr("document.getElementById('viewer-coords')?.innerText");
  console.log(`Post-W Fly Coords: "${postWCoords}"`);

  for (let step = 0; step < 8; step++) {
    await send("Input.dispatchKeyEvent", { type: "rawKeyDown", windowsVirtualKeyCode: 68, code: "KeyD", key: "d" });
    await sleep(80);
    await send("Input.dispatchKeyEvent", { type: "keyUp", windowsVirtualKeyCode: 68, code: "KeyD", key: "d" });
    await sleep(40);
  }
  await sleep(600);

  const postDCoords = await evalExpr("document.getElementById('viewer-coords')?.innerText");
  console.log(`Post-D Strafe Coords: "${postDCoords}"`);

  // Screenshot 3D Viewer Experience
  const viewerScreenshot = await send("Page.captureScreenshot", { format: "png" });
  if (viewerScreenshot.result?.data) {
    const buf = Buffer.from(viewerScreenshot.result.data, 'base64');
    const path = resolve("docs", "web_viewer_verification.png");
    writeFileSync(path, buf);
    console.log(`3D Viewer screenshot saved: ${path} (${buf.length} bytes)`);
  }

  // ── 6. Test "Return to Overview" Button ────────────────────────────────────
  console.log("\n--- Testing Return to Overview Navigation ---");
  await evalExpr("document.getElementById('viewer-btn-back').click()");
  await sleep(1000);

  const landingRestored = await evalExpr("!document.getElementById('landing-view')?.classList.contains('view-hidden')");
  const viewerClosed = await evalExpr("document.getElementById('viewer-view')?.classList.contains('view-hidden')");
  console.log(`Returned to Landing Page: ${landingRestored && viewerClosed}`);

  // Summary
  console.log("\n=== NAMMA SPACE WEB EXPERIENCE VALIDATION SUMMARY ===");
  console.log(`1. Landing Page Rendered:      ${!landingHidden && workflowCardCount === 4}`);
  console.log(`2. 3D Viewer Launch:           ${!viewerHidden && loaded}`);
  console.log(`3. Initial Telemetry Pose:     ${initialCoords}`);
  console.log(`4. Mouse Orbit Delta:          ${initialCoords !== postMouseCoords}`);
  console.log(`5. WASD Fly Navigation Delta:  ${postMouseCoords !== postWCoords || postWCoords !== postDCoords}`);
  console.log(`6. Return to Overview State:   ${landingRestored && viewerClosed}`);

  ws.close();
  chromeProc.kill();
  process.exit(0);
}

runTest().catch((err) => {
  console.error("Test failed with error:", err);
  chromeProc.kill();
  process.exit(1);
});
