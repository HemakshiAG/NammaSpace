import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "http://127.0.0.1:8080/index.html";

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9231",
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
      const res = await fetch("http://127.0.0.1:9231/json");
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

  // Trigger launch viewer directly using Namma's normal app workflow
  await evalExpr(`(() => {
    window.location.hash = '#pipeline';
    document.getElementById('landing-view').classList.add('view-hidden');
    document.getElementById('viewer-view').classList.remove('view-hidden');
    if (window.app && window.app.viewer) {
      window.app.viewer.load();
    }
  })()`);

  // Wait 4 seconds for full splat load & render
  await sleep(4000);

  const coords = await evalExpr(`document.getElementById('viewer-coords')?.textContent`);
  console.log("HUD Coordinates:", coords);

  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (shot.result?.data) {
    writeFileSync("scratch/user_view_verification.png", Buffer.from(shot.result.data, 'base64'));
    console.log("Saved scratch/user_view_verification.png");
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

