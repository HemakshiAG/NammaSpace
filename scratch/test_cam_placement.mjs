import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const TARGET_URL = "http://127.0.0.1:8080/index.html";

const chromeProc = spawn(CHROME_PATH, [
  "--remote-debugging-port=9232",
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
      const res = await fetch("http://127.0.0.1:9232/json");
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

  // Read cameras.json to get initial camera
  const camInfo = await evalExpr(`(async () => {
    const r = await fetch('./cameras.json');
    const d = await r.json();
    const cam = d.cameras[d.initial || 0];
    return {
      pos: cam.pos,
      lookAt: [cam.pos[0] + cam.forward[0]*2, cam.pos[1] + cam.forward[1]*2, cam.pos[2] + cam.forward[2]*2]
    };
  })()`);

  console.log("Cam info from cameras.json:", camInfo);

  // Render with camera from cameras.json
  const res = await evalExpr(`(async () => {
    const GaussianSplats3D = await import('https://cdn.jsdelivr.net/npm/@mkkellogg/gaussian-splats-3d@0.4.6/build/gaussian-splats-3d.module.js');
    const container = document.getElementById('canvas-container');
    container.innerHTML = '';
    document.getElementById('landing-view').classList.add('view-hidden');
    document.getElementById('viewer-view').classList.remove('view-hidden');
    
    const camPos = ${JSON.stringify(camInfo.pos)};
    const camLookAt = ${JSON.stringify(camInfo.lookAt)};
    
    const viewer = new GaussianSplats3D.Viewer({
      cameraUp: [0, -1, 0],
      initialCameraPosition: camPos,
      initialCameraLookAt: camLookAt,
      selfDrivenMode: true,
      useBuiltInControls: true,
      rootElement: container
    });
    
    await viewer.addSplatScene('./scene.splat', {
      format: GaussianSplats3D.SceneFormat.Splat,
      splatAlphaRemovalThreshold: 5,
      showLoadingUI: false
    });
    
    viewer.start();
    await new Promise(r => setTimeout(r, 2000));
    
    const cam = viewer.camera;
    return {
      pos: [cam.position.x, cam.position.y, cam.position.z],
      splatCount: viewer.splatMesh.getSplatCount()
    };
  })()`);

  console.log("Viewer Render Result:", res);

  // Capture screenshot
  const shot = await send("Page.captureScreenshot", { format: "png" });
  if (shot.result?.data) {
    writeFileSync("scratch/cam_placed_screen.png", Buffer.from(shot.result.data, 'base64'));
    console.log("Saved scratch/cam_placed_screen.png");
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

