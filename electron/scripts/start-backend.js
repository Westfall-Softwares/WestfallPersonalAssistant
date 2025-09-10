/* eslint-disable no-console */
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const http = require("http");
const net = require("net");

async function findFreePort(start = 8756, tries = 25) {
  let port = start;
  for (let i = 0; i < tries; i++, port++) {
    // eslint-disable-next-line no-await-in-loop
    const free = await new Promise((resolve) => {
      const srv = net.createServer();
      srv.once("error", () => resolve(false));
      srv.once("listening", () => srv.close(() => resolve(true)));
      srv.listen(port, "127.0.0.1");
    });
    if (free) return port;
  }
  throw new Error("No free port found");
}

function httpGet(url, timeoutMs) {
  return new Promise((resolve, reject) => {
    const req = http.get(url, (res) => {
      let data = "";
      res.on("data", (c) => (data += c));
      res.on("end", () => resolve({ status: res.statusCode, body: data }));
    });
    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error("timeout"));
    });
    req.on("error", reject);
  });
}

async function waitForHealth(baseUrl, totalTimeoutMs = 20000) {
  const start = Date.now();
  let delay = 300;
  while (Date.now() - start < totalTimeoutMs) {
    try {
      const { status, body } = await httpGet(`${baseUrl}/health`, 2500);
      if (status === 200 && body.includes('"ok"') || body.includes('"status":"ok"')) {
        return true;
      }
    } catch (_) {}
    // backoff
    // eslint-disable-next-line no-await-in-loop
    await new Promise((r) => setTimeout(r, delay));
    delay = Math.min(delay * 1.5, 1500);
  }
  throw new Error("Backend health check timed out");
}

function resolveBackendBinary() {
  // Packaged app path (process.resourcesPath) → app.asar/resources/backend
  const resources = process.resourcesPath || path.join(__dirname, "..", "..");
  const packagedDir = path.join(resources, "backend");

  // Common names produced by PyInstaller
  const candidates = process.platform === "win32"
    ? ["westfall-backend.exe", "backend.exe", "app.exe"]
    : ["westfall-backend", "backend", "app"];

  // 1) packaged location
  for (const name of candidates) {
    const p = path.join(packagedDir, name);
    if (fs.existsSync(p)) return p;
  }

  // 2) dev fallback: project root ../dist-backend/...
  const devDir = path.resolve(__dirname, "..", "..", "dist-backend");
  for (const name of candidates) {
    const p = path.join(devDir, name);
    if (fs.existsSync(p)) return p;
  }

  // 3) fallback: first executable file within packagedDir or devDir
  for (const dir of [packagedDir, devDir]) {
    if (fs.existsSync(dir)) {
      const files = fs.readdirSync(dir);
      for (const f of files) {
        const full = path.join(dir, f);
        try {
          if (fs.statSync(full).isFile() && fs.accessSync(full, fs.constants.X_OK) == null) {
            return full;
          }
        } catch (_) {}
      }
    }
  }
  throw new Error("Backend binary not found. Ensure dist-backend/* exists and is copied via extraResources.");
}

async function startBackend() {
  const port = await findFreePort(8756, 30);
  const host = "127.0.0.1";
  const url = `http://${host}:${port}`;
  const bin = resolveBackendBinary();

  const env = {
    ...process.env,
    WESTFALL_HOST: host,
    WESTFALL_PORT: String(port),
  };

  const proc = spawn(bin, [], {
    env,
    windowsHide: true,
    stdio: ["ignore", "pipe", "pipe"],
  });

  proc.stdout.on("data", (d) => console.log("[backend]", d.toString().trim()));
  proc.stderr.on("data", (d) => console.warn("[backend:err]", d.toString().trim()));
  proc.on("exit", (code) => console.log("[backend] exited:", code));

  await waitForHealth(url, 20000);
  return { proc, url };
}

function killBackend(proc) {
  if (!proc || proc.killed) return;
  try {
    if (process.platform === "win32") {
      spawn("taskkill", ["/pid", String(proc.pid), "/f", "/t"]);
    } else {
      proc.kill("SIGTERM");
      setTimeout(() => proc.kill("SIGKILL"), 2000);
    }
  } catch (e) {
    console.warn("Failed to kill backend:", e.message);
  }
}

module.exports = { startBackend, killBackend };
#!/usr/bin/env node
// Placeholder: in a future commit, spawn the packaged backend binary and wait for /health.
// For now, keep this stub so the Electron app structure is complete.