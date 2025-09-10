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
    console.log("Loading backend URL:", backendUrl);
    mainWindow.loadURL(backendUrl);
  } else {
    console.log("No backend URL, loading fallback HTML");
    // Fallback to local HTML if backend isn't available
    mainWindow.loadFile(path.join(__dirname, "renderer", "index.html"));
  }
  
  mainWindow.on("closed", () => { mainWindow = null; });
}

app.whenReady().then(async () => {
  const gotLock = app.requestSingleInstanceLock();
  if (!gotLock) { app.quit(); return; }

  try {
    console.log("Starting backend...");
    const res = await startBackend();
    backendProc = res.proc;
    backendUrl = res.url;
    console.log("Backend started successfully at:", backendUrl);
  } catch (e) {
    console.error("Backend failed to start:", e);
    backendUrl = null; // Ensure fallback is used
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