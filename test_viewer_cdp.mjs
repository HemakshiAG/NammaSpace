// Automated 3D Viewer Navigation Test via Chrome DevTools Protocol (CDP)
import { writeFileSync } from 'fs';
import { spawn } from 'child_process';
import { resolve } from 'path';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PROFILE_DIR = resolve(process.env.TEMP || "C:\\temp", "chrome_cdp_profile_test");
const TARGET_URL = "http://127.0.0.1:8080/index.html";

console.log("=== Starting Automated Viewer Validation via Native CDP ===");

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9222",
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
      const res = await fetch("http://127.0.0.1:9222/json");
      if (res.ok) {
        const pages = await res.json();
        const page = pages.find(p => p.type === 'page' && p.url.includes("8080"));
        if (page && page.webSocketDebuggerUrl) {
          wsUrl = page.webSocketDebuggerUrl;
          console.log("Connected to Chrome target:", page.title, page.url);
          break;
        }
      }
    } catch (_) {}
  }

  if (!wsUrl) {
    console.error("Could not find WebSocket debugger URL on port 9222");
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

  console.log("Waiting for scene to finish downloading and rendering...");
  let loaded = false;
  for (let i = 0; i < 60; i++) {
    await sleep(1000);
    const loadingDisplay = await evalExpr("document.getElementById('loading')?.style.display");
    const statusText = await evalExpr("document.getElementById('loading-status')?.innerText");
    const coords = await evalExpr("document.getElementById('coords')?.innerText");
    const readyState = await evalExpr("document.readyState");

    console.log(`[${i}s] Ready: "${readyState}" | Status: "${statusText}" | Loading Display: "${loadingDisplay}" | Coords: "${coords}"`);

    if (loadingDisplay === 'none' && coords && coords.includes('x:')) {
      loaded = true;
      break;
    }
  }

  // 1. Initial State
  const initialRoom = await evalExpr("document.getElementById('room-name')?.innerText");
  const initialCoords = await evalExpr("document.getElementById('coords')?.innerText");
  console.log(`\nInitial Room Title: "${initialRoom}"`);
  console.log(`Initial Coordinates: "${initialCoords}"`);

  // 2. Mouse Orbit / Drag interaction
  console.log("\n--- Testing Mouse Drag (Orbit) ---");
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x: 640, y: 360, button: "left", clickCount: 1 });
  for (let x = 640; x >= 440; x -= 20) {
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x, y: 360, button: "left" });
    await sleep(30);
  }
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: 440, y: 360, button: "left" });
  await sleep(1000);

  const postMouseCoords = await evalExpr("document.getElementById('coords')?.innerText");
  console.log(`Post-Mouse Orbit Coordinates: "${postMouseCoords}"`);

  // 3. WASD Key: 'W' (Forward Fly)
  console.log("\n--- Testing 'W' Key (Forward Fly) ---");
  for (let step = 0; step < 10; step++) {
    await send("Input.dispatchKeyEvent", { type: "rawKeyDown", windowsVirtualKeyCode: 87, code: "KeyW", key: "w" });
    await sleep(80);
    await send("Input.dispatchKeyEvent", { type: "keyUp", windowsVirtualKeyCode: 87, code: "KeyW", key: "w" });
    await sleep(40);
  }
  await sleep(1000);

  const postWCoords = await evalExpr("document.getElementById('coords')?.innerText");
  console.log(`Post-W Key Coordinates: "${postWCoords}"`);

  // 4. WASD Key: 'D' (Right Strafe)
  console.log("\n--- Testing 'D' Key (Strafe Right) ---");
  for (let step = 0; step < 10; step++) {
    await send("Input.dispatchKeyEvent", { type: "rawKeyDown", windowsVirtualKeyCode: 68, code: "KeyD", key: "d" });
    await sleep(80);
    await send("Input.dispatchKeyEvent", { type: "keyUp", windowsVirtualKeyCode: 68, code: "KeyD", key: "d" });
    await sleep(40);
  }
  await sleep(1000);

  const postDCoords = await evalExpr("document.getElementById('coords')?.innerText");
  console.log(`Post-D Key Coordinates: "${postDCoords}"`);

  // 5. Capture Verification Screenshot
  console.log("\n--- Capturing Verification Screenshot ---");
  const screenshot = await send("Page.captureScreenshot", { format: "png" });
  if (screenshot.result?.data) {
    const buf = Buffer.from(screenshot.result.data, 'base64');
    const screenshotPath = resolve("docs", "viewer_roaming_verification.png");
    writeFileSync(screenshotPath, buf);
    console.log(`Screenshot saved to: ${screenshotPath} (${buf.length} bytes)`);
  }

  // Summary Verification
  console.log("\n=== CONTROL VALIDATION SUMMARY ===");
  console.log(`Initial:    ${initialCoords}`);
  console.log(`Post-Mouse: ${postMouseCoords}`);
  console.log(`Post-W:     ${postWCoords}`);
  console.log(`Post-D:     ${postDCoords}`);

  const mouseMoved = initialCoords !== postMouseCoords;
  const wasdMoved = postMouseCoords !== postWCoords || postWCoords !== postDCoords;
  console.log(`Mouse Orbit Verified: ${mouseMoved}`);
  console.log(`WASD Fly Verified:    ${wasdMoved}`);

  ws.close();
  chromeProc.kill();
  process.exit(0);
}

runTest().catch((err) => {
  console.error("Test failed with error:", err);
  chromeProc.kill();
  process.exit(1);
});
