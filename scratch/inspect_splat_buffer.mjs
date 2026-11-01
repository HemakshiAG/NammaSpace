import { spawn } from 'child_process';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "http://127.0.0.1:8080/index.html";

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9229",
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
      const res = await fetch("http://127.0.0.1:9229/json");
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
  console.log("Inspecting splat buffer directly in Chrome...");

  const res = await evalExpr(`(async () => {
    const GaussianSplats3D = await import('https://cdn.jsdelivr.net/npm/@mkkellogg/gaussian-splats-3d@0.4.6/build/gaussian-splats-3d.module.js');
    const resp = await fetch('./scene.splat');
    const arrayBuffer = await resp.arrayBuffer();
    const loader = new GaussianSplats3D.SplatLoader();
    const splatBuffer = loader.parseSplatBuffer(arrayBuffer);
    
    // Read first splat
    const position = new Float32Array(3);
    const scale = new Float32Array(3);
    const rotation = new Float32Array(4);
    const color = new Uint8Array(4);
    
    const count = splatBuffer.getSplatCount();
    const sample = [];
    for (let i = 0; i < Math.min(5, count); i++) {
      splatBuffer.getPosition(i, position);
      splatBuffer.getScale(i, scale);
      splatBuffer.getRotation(i, rotation);
      splatBuffer.getColor(i, color);
      sample.push({
        idx: i,
        pos: [position[0], position[1], position[2]],
        scale: [scale[0], scale[1], scale[2]],
        rot: [rotation[0], rotation[1], rotation[2], rotation[3]],
        color: [color[0], color[1], color[2], color[3]]
      });
    }

    return {
      byteLength: arrayBuffer.byteLength,
      splatCount: count,
      sample: sample
    };
  })()`);

  console.log("Parsed Splat Data:", JSON.stringify(res, null, 2));

  ws.close();
  chromeProc.kill();
  process.exit(0);
}

run().catch(e => {
  console.error(e);
  chromeProc.kill();
  process.exit(1);
});

