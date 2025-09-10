const { app, BrowserWindow } = require("electron");
const path = require("path");
const { startBackend, killBackend } = require("./scripts/start-backend");

let backendProc = null;
let backendUrl = null;
let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 780,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      sandbox: true
    }
  });
  mainWindow.removeMenu();
  
  // Load the backend web interface instead of local HTML
  if (backendUrl) {
    mainWindow.loadURL(backendUrl);
  } else {
    // Fallback to local HTML if backend isn't available
    mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
  }
  
  mainWindow.on("closed", () => { mainWindow = null; });
}

app.whenReady().then(async () => {
  const gotLock = app.requestSingleInstanceLock();
  if (!gotLock) { app.quit(); return; }

  try {
    const res = await startBackend();
    backendProc = res.proc;
    backendUrl = res.url;
    // Optionally pass backendUrl to renderer via file or global
  } catch (e) {
    console.error("Backend failed to start:", e);
  }

  createWindow();
});

app.on("before-quit", () => {
  killBackend(backendProc);
});

app.on("window-all-closed", () => {
  // Keep running if you later add tray; otherwise quit on non-mac
  if (process.platform !== "darwin") app.quit();
});