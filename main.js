const { app, BrowserWindow, ipcMain, dialog, systemPreferences } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');

// Enable live reload for development
if (process.env.NODE_ENV === 'development') {
  require('electron-reload')(__dirname, {
    electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
    hardResetMethod: 'exit'
  });
}

const store = new Store();
let mainWindow;
let backendProcess = null;

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    icon: path.join(__dirname, 'westfall.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    titleBarStyle: 'default',
    show: false
  });

  // Load the React app
  const isDev = process.env.NODE_ENV === 'development';
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
  });
}

// App event handlers
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for model management
ipcMain.handle('select-model-file', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select AI Model File',
    filters: [
      { name: 'Model Files', extensions: ['gguf', 'ggml', 'bin', 'pt', 'pth', 'safetensors'] },
      { name: 'All Files', extensions: ['*'] }
    ],
    properties: ['openFile']
  });

  if (!result.canceled && result.filePaths.length > 0) {
    const modelPath = result.filePaths[0];
    store.set('lastModelPath', modelPath);
    return modelPath;
  }
  return null;
});

ipcMain.handle('get-last-model', () => {
  return store.get('lastModelPath', null);
});

ipcMain.handle('start-model-server', async (event, modelPath) => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
  }

  return new Promise((resolve, reject) => {
    try {
      backendProcess = spawn('python', [
        path.join(__dirname, 'backend', 'server.py'),
        '--model', modelPath
      ], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      backendProcess.stdout.on('data', (data) => {
        console.log(`Backend: ${data}`);
        if (data.toString().includes('Server started')) {
          resolve(true);
        }
      });

      backendProcess.stderr.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
      });

      backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
        backendProcess = null;
      });

      // Timeout after 30 seconds
      setTimeout(() => {
        if (backendProcess) {
          reject(new Error('Server startup timeout'));
        }
      }, 30000);

    } catch (error) {
      reject(error);
    }
  });
});

ipcMain.handle('stop-model-server', () => {
  if (backendProcess) {
    backendProcess.kill();
    backendProcess = null;
    return true;
  }
  return false;
});

// GPU information
ipcMain.handle('get-gpu-info', async () => {
  // This would need to be expanded with actual GPU detection
  // For now, return placeholder info
  return {
    hasGPU: true,
    gpuName: 'NVIDIA GeForTX RTX 2060',
    vramTotal: '6GB',
    vramAvailable: '5.2GB'
  };
});

// Settings management
ipcMain.handle('get-settings', () => {
  return store.get('settings', {
    thinkingMode: 'normal',
    theme: 'dark',
    autoStart: false,
    gpuLayers: 'auto'
  });
});

ipcMain.handle('save-settings', (event, settings) => {
  store.set('settings', settings);
  return true;
});

// Screen capture (placeholder - would need platform-specific implementation)
ipcMain.handle('capture-screen', async () => {
  // This would integrate with native screen capture APIs
  return {
    success: false,
    message: 'Screen capture not yet implemented'
  };
});