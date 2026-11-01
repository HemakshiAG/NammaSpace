import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "http://127.0.0.1:8080/index.html";

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9235",
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
      const res = await fetch("http://127.0.0.1:9235/json");
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

  // Directly load scene.splat.prev with camera at [0.470, -0.467, -5.779]
  const renderRes = await evalExpr(`(async () => {
    const GaussianSplats3D = await import('https://cdn.jsdelivr.net/npm/@mkkellogg/gaussian-splats-3d@0.4.6/build/gaussian-splats-3d.module.js');
    const container = document.getElementById('canvas-container');
    container.innerHTML = '';
    document.getElementById('landing-view').classList.add('view-hidden');
    document.getElementById('viewer-view').classList.remove('view-hidden');

    const camPos = [0.470, -0.467, -5.779];
    const camLookAt = [0.470, -0.467, 0.0];

    const viewer = new GaussianSplats3D.Viewer({
      cameraUp: [0, -1, 0],
      initialCameraPosition: camPos,
      initialCameraLookAt: camLookAt,
      selfDrivenMode: true,
      useBuiltInControls: true,
      rootElement: container
    });

    await viewer.addSplatScene('./scene.splat.prev', {
      format: GaussianSplats3D.SceneFormat.Splat,
      splatAlphaRemovalThreshold: 5,
      showLoadingUI: false
    });

    viewer.start();
    await new Promise(r => setTimeout(r, 2500));

    return {
      splatCount: viewer.splatMesh.getSplatCount()
    };
  })()`);

  console.log("Render Result:", renderRes);

  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (shot.result?.data) {
    writeFileSync("scratch/prev_splat_screen.png", Buffer.from(shot.result.data, 'base64'));
    console.log("Saved scratch/prev_splat_screen.png");
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

