import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "http://127.0.0.1:8080/index.html";

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9228",
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
      const res = await fetch("http://127.0.0.1:9228/json");
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
  console.log("Clicking hero launch button...");
  await evalExpr("document.getElementById('hero-btn-launch').click()");

  // Wait until loading overlay is hidden
  for (let i = 0; i < 30; i++) {
    await sleep(1000);
    const loadingHidden = await evalExpr("document.getElementById('viewer-loading')?.style.display === 'none'");
    const status = await evalExpr("document.getElementById('loading-status-detail')?.innerText");
    console.log(`[${i}s] Loading status: ${status}, hidden: ${loadingHidden}`);
    if (loadingHidden) break;
  }

  // Find canvas and its properties
  const debugInfo = await evalExpr(`(() => {
    const canvases = Array.from(document.querySelectorAll('canvas'));
    return {
      canvasesCount: canvases.length,
      details: canvases.map(c => ({
        parent: c.parentElement?.id || c.parentElement?.tagName,
        width: c.width,
        height: c.height,
        style: c.getAttribute('style')
      }))
    };
  })()`);

  console.log("Canvas Debug Info:", JSON.stringify(debugInfo, null, 2));

  // Capture screenshot
  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (shot.result?.data) {
    writeFileSync("scratch/debug_screen_loaded.png", Buffer.from(shot.result.data, 'base64'));
    console.log("Saved scratch/debug_screen_loaded.png");
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

