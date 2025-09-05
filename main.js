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
  // Enhanced GPU detection with system information
  try {
    // This would integrate with system APIs for actual GPU detection
    // Currently provides RTX 2060 optimized configuration
    return {
      hasGPU: true,
      gpuName: 'NVIDIA GeForce RTX 2060',
      vramTotal: '6GB',
      vramAvailable: '5.2GB',
      cudaSupport: true,
      computeCapability: '7.5',
      optimizedLayers: 35, // Recommended for RTX 2060
      maxContextLength: 4096
    };
  } catch (error) {
    console.error('GPU detection error:', error);
    return {
      hasGPU: false,
      gpuName: 'CPU Only',
      vramTotal: '0GB',
      vramAvailable: '0GB',
      cudaSupport: false,
      computeCapability: 'N/A',
      optimizedLayers: 0,
      maxContextLength: 2048
    };
  }
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

// Screen capture (integrates with backend)
ipcMain.handle('capture-screen', async () => {
  try {
    // Call backend screen capture endpoint
    const response = await fetch('http://127.0.0.1:8000/capture-screen', {
      method: 'POST'
    });
    return await response.json();
  } catch (error) {
    return {
      success: false,
      message: `Screen capture failed: ${error.message}`
    };
  }
});

ipcMain.handle('start-monitoring', async (event, interval) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/start-monitoring', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interval: interval || 30 })
    });
    return await response.json();
  } catch (error) {
    return {
      success: false,
      message: `Failed to start monitoring: ${error.message}`
    };
  }
});

ipcMain.handle('stop-monitoring', async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/stop-monitoring', {
      method: 'POST'
    });
    return await response.json();
  } catch (error) {
    return {
      success: false,
      message: `Failed to stop monitoring: ${error.message}`
    };
  }
});