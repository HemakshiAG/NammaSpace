import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "http://127.0.0.1:8080/index.html";

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9227",
  "--headless=new",
  "--use-gl=angle",
  "--use-angle=d3d11",
  "--window-size=1280,720",
  TARGET_URL
]);

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

async function run() {
  let wsUrl = null;
  for (let i = 0; i < 20; i++) {
    await sleep(500);
    try {
      const res = await fetch("http://127.0.0.1:9227/json");
      if (res.ok) {
        const pages = await res.json();
        const p = pages.find(x => x.type === 'page');
        if (p && p.webSocketDebuggerUrl) {
          wsUrl = p.webSocketDebuggerUrl;
          break;
        }
      }
    } catch (_) {}
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
  await send("Page.enable");
  await send("Runtime.enable");

  const evalExpr = async (expr) => {
    const res = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    return res.result?.result?.value;
  };

  await sleep(1000);
  console.log("Triggering showViewer...");
  await evalExpr("document.getElementById('hero-btn-launch').click()");

  // Wait 4 seconds for splat scene to load
  await sleep(4000);

  // Inspect the canvas pixels directly!
  const canvasStats = await evalExpr(`(() => {
    const canvas = document.querySelector('#canvas-container canvas');
    if (!canvas) return { error: "No canvas element" };
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) return { error: "No WebGL context" };
    const w = canvas.width, h = canvas.height;
    const pixels = new Uint8Array(w * h * 4);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    
    let nonZero = 0;
    let rSum = 0, gSum = 0, bSum = 0;
    for (let i = 0; i < pixels.length; i += 4) {
      if (pixels[i] > 10 || pixels[i+1] > 10 || pixels[i+2] > 10) {
        nonZero++;
        rSum += pixels[i];
        gSum += pixels[i+1];
        bSum += pixels[i+2];
      }
    }
    return {
      width: w,
      height: h,
      totalPixels: w * h,
      renderedPixels: nonZero,
      renderPct: (nonZero / (w * h) * 100).toFixed(2) + "%",
      avgColor: nonZero > 0 ? [Math.round(rSum/nonZero), Math.round(gSum/nonZero), Math.round(bSum/nonZero)] : [0,0,0]
    };
  })()`);

  console.log("Canvas Stats:", JSON.stringify(canvasStats, null, 2));

  // Take screenshot
  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (shot.result?.data) {
    writeFileSync("scratch/debug_screen.png", Buffer.from(shot.result.data, 'base64'));
    console.log("Screenshot saved to scratch/debug_screen.png");
  }

  ws.close();
  chromeProc.kill();
  process.exit(0);
}

run().catch(e => {
  console.error(e);
  chromeProc.kill();
  process.exit(1);
});

