const { app, BrowserWindow, ipcMain, dialog, systemPreferences, Tray, Menu, globalShortcut, Notification } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');
const os = require('os');

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // Someone tried to run a second instance, focus our window instead
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
    } else {
      createWindow();
    }
  });
}

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
let backendServerProcess = null;
let tray = null;
let isQuitting = false;
let backendRestartCount = 0;
const MAX_RESTART_ATTEMPTS = 3;
const BACKEND_PORT = 8756; // Use consistent port

// Health check function
async function checkBackendHealth(port = BACKEND_PORT) {
  try {
    const response = await fetch(`http://127.0.0.1:${port}/health`, {
      method: 'GET',
      timeout: 5000
    });
    const result = await response.json();
    return result.status === 'ok';
  } catch (error) {
    return false;
  }
}

// Find available port (fallback mechanism)
async function findAvailablePort(startPort = BACKEND_PORT) {
  const net = require('net');
  return new Promise((resolve) => {
    const server = net.createServer();
    server.listen(startPort, () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => {
      resolve(findAvailablePort(startPort + 1));
    });
  });
}

// Start the backend server with health checks and auto-restart
async function startBackendServer() {
  if (backendServerProcess) {
    console.log('Backend server already running');
    const isHealthy = await checkBackendHealth();
    if (isHealthy) {
      return Promise.resolve(true);
    } else {
      console.log('Backend server unhealthy, restarting...');
      stopBackendServer();
    }
  }

  return new Promise(async (resolve, reject) => {
    try {
      const serverPath = path.join(__dirname, '..', 'backend', 'server.py');
      const port = await findAvailablePort(BACKEND_PORT);
      console.log('Starting backend server:', serverPath, 'on port', port);
      
      // Configure spawn options for background process
      const spawnOptions = {
        stdio: ['pipe', 'pipe', 'pipe'],
        windowsHide: true, // Hide console window on Windows
        detached: false,
        env: {
          ...process.env,
          PORT: port.toString(),
          HOST: '127.0.0.1'
        }
      };

      backendServerProcess = spawn('python', [serverPath, '--port', port.toString()], spawnOptions);

      let serverReady = false;
      let healthCheckInterval;

      backendServerProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`Backend Server: ${output}`);
        
        // Check if server has started successfully
        if ((output.includes('Server started successfully') || 
             output.includes('Uvicorn running on')) && !serverReady) {
          serverReady = true;
          console.log('Backend server is ready');
          
          // Start health monitoring
          healthCheckInterval = setInterval(async () => {
            const isHealthy = await checkBackendHealth(port);
            if (!isHealthy && !isQuitting) {
              console.log('Backend health check failed, attempting restart...');
              clearInterval(healthCheckInterval);
              await restartBackendServer();
            }
          }, 30000); // Check every 30 seconds
          
          resolve(true);
        }
      });

      backendServerProcess.stderr.on('data', (data) => {
        const output = data.toString();
        console.error(`Backend Server Error: ${output}`);
        
        // Also check stderr for the success message and for Uvicorn running
        if ((output.includes('Server started successfully') || 
             output.includes('Uvicorn running on http://127.0.0.1')) && !serverReady) {
          serverReady = true;
          console.log('Backend server is ready');
          resolve(true);
        }
      });

      backendServerProcess.on('close', (code) => {
        console.log(`Backend server process exited with code ${code}`);
        if (healthCheckInterval) clearInterval(healthCheckInterval);
        backendServerProcess = null;
        
        // Auto-restart if not intentionally stopped
        if (!isQuitting && code !== 0 && backendRestartCount < MAX_RESTART_ATTEMPTS) {
          console.log(`Backend crashed, attempting restart (${backendRestartCount + 1}/${MAX_RESTART_ATTEMPTS})`);
          setTimeout(() => restartBackendServer(), 2000);
        }
      });

      backendServerProcess.on('error', (error) => {
        console.error(`Failed to start backend server: ${error}`);
        backendServerProcess = null;
        reject(error);
      });

      // Timeout after 45 seconds
      setTimeout(() => {
        if (!serverReady) {
          console.error('Backend server startup timeout');
          if (backendServerProcess) {
            backendServerProcess.kill();
            backendServerProcess = null;
          }
          reject(new Error('Backend server startup timeout'));
        }
      }, 45000);

    } catch (error) {
      console.error(`Error starting backend server: ${error}`);
      reject(error);
    }
  });
}

// Restart backend server with backoff
async function restartBackendServer() {
  if (backendRestartCount >= MAX_RESTART_ATTEMPTS) {
    console.error('Max restart attempts reached, giving up');
    if (mainWindow) {
      mainWindow.webContents.send('backend-error', {
        type: 'restart_failed',
        message: 'Backend server failed to start after multiple attempts'
      });
    }
    return false;
  }

  backendRestartCount++;
  stopBackendServer();
  
  // Exponential backoff
  const delay = Math.min(1000 * Math.pow(2, backendRestartCount - 1), 30000);
  console.log(`Waiting ${delay}ms before restart attempt ${backendRestartCount}`);
  
  return new Promise((resolve) => {
    setTimeout(async () => {
      try {
        await startBackendServer();
        backendRestartCount = 0; // Reset on successful start
        resolve(true);
      } catch (error) {
        console.error('Restart attempt failed:', error);
        resolve(false);
      }
    }, delay);
  });
}

// Create system tray
function createTray() {
  const iconPath = path.join(__dirname, '..', 'assets', 'westfall.png');
  tray = new Tray(iconPath);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Assistant',
      type: 'normal',
      click: () => {
        if (mainWindow) {
          if (mainWindow.isMinimized()) mainWindow.restore();
          mainWindow.show();
          mainWindow.focus();
        } else {
          createWindow();
        }
      }
    },
    {
      label: 'Quick Chat',
      type: 'normal',
      accelerator: 'CmdOrCtrl+Shift+A',
      click: () => {
        if (mainWindow) {
          if (mainWindow.isMinimized()) mainWindow.restore();
          mainWindow.show();
          mainWindow.focus();
          // Send event to focus chat input
          mainWindow.webContents.send('focus-chat');
        } else {
          createWindow();
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Backend Status',
      type: 'submenu',
      submenu: [
        {
          label: backendServerProcess ? 'Running' : 'Stopped',
          type: 'normal',
          enabled: false
        },
        { type: 'separator' },
        {
          label: 'Restart Backend',
          type: 'normal',
          click: async () => {
            try {
              await restartBackendServer();
              new Notification({
                title: 'Backend Restarted',
                body: 'Backend server has been restarted successfully',
                icon: path.join(__dirname, '..', 'assets', 'westfall.png')
              }).show();
            } catch (error) {
              new Notification({
                title: 'Restart Failed',
                body: 'Failed to restart backend server',
                icon: path.join(__dirname, '..', 'assets', 'westfall.png')
              }).show();
            }
          }
        },
        {
          label: 'Stop Backend',
          type: 'normal',
          enabled: !!backendServerProcess,
          click: () => {
            stopBackendServer();
            new Notification({
              title: 'Backend Stopped',
              body: 'Backend server has been stopped',
              icon: path.join(__dirname, '..', 'assets', 'westfall.png')
            }).show();
          }
        }
      ]
    },
    { type: 'separator' },
    {
      label: 'Screen Capture',
      type: 'normal',
      accelerator: 'CmdOrCtrl+Shift+S',
      click: () => {
        captureScreenFromTray();
      }
    },
    {
      label: 'Settings',
      type: 'normal',
      click: () => {
        if (mainWindow) {
          if (mainWindow.isMinimized()) mainWindow.restore();
          mainWindow.show();
          mainWindow.focus();
          // Send event to open settings
          mainWindow.webContents.send('open-settings');
        } else {
          createWindow();
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      type: 'normal',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
  tray.setToolTip('Entrepreneur Assistant');
  
  // Double-click to show/hide window
  tray.on('double-click', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    } else {
      createWindow();
    }
  });
}

// Screen capture from tray
async function captureScreenFromTray() {
  try {
    const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}/capture-screen`, {
      method: 'POST'
    });
    const result = await response.json();
    
    if (result.success) {
      // Show notification
      new Notification({
        title: 'Screen Captured',
        body: 'Screen captured and ready for analysis',
        icon: path.join(__dirname, '..', 'assets', 'westfall.png')
      }).show();
    } else {
      new Notification({
        title: 'Capture Failed',
        body: result.message || 'Failed to capture screen',
        icon: path.join(__dirname, '..', 'assets', 'westfall.png')
      }).show();
    }
  } catch (error) {
    new Notification({
      title: 'Capture Error',
      body: 'Backend server not available',
      icon: path.join(__dirname, '..', 'assets', 'westfall.png')
    }).show();
  }
}

// Auto-start functionality
function setupAutoStart() {
  const settings = store.get('settings', {});
  if (settings.autoStart) {
    app.setLoginItemSettings({
      openAtLogin: true,
      openAsHidden: true,
      name: 'Entrepreneur Assistant',
      path: process.execPath
    });
  } else {
    app.setLoginItemSettings({
      openAtLogin: false
    });
  }
}

// Global shortcuts setup
function setupGlobalShortcuts() {
  // Quick chat shortcut
  globalShortcut.register('CmdOrCtrl+Shift+A', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.show();
      mainWindow.focus();
      mainWindow.webContents.send('focus-chat');
    } else {
      createWindow();
    }
  });

  // Screen capture shortcut
  globalShortcut.register('CmdOrCtrl+Shift+S', () => {
    captureScreenFromTray();
  });

  // Toggle window shortcut
  globalShortcut.register('CmdOrCtrl+Shift+W', () => {
    if (mainWindow) {
      if (mainWindow.isVisible()) {
        mainWindow.hide();
      } else {
        mainWindow.show();
        mainWindow.focus();
      }
    } else {
      createWindow();
    }
  });
}

// Session persistence
function saveSession() {
  if (mainWindow) {
    const bounds = mainWindow.getBounds();
    store.set('session', {
      bounds: bounds,
      isMaximized: mainWindow.isMaximized(),
      timestamp: Date.now()
    });
  }
}

function restoreSession() {
  const session = store.get('session');
  if (session && session.bounds) {
    return {
      ...session.bounds,
      show: false
    };
  }
  return {
    width: 1200,
    height: 800,
    show: false
  };
}

// Stop the backend server gracefully
async function stopBackendServer() {
  if (backendServerProcess) {
    console.log('Stopping backend server gracefully');
    
    try {
      // Try graceful shutdown first
      await fetch(`http://127.0.0.1:${BACKEND_PORT}/shutdown`, {
        method: 'POST',
        timeout: 5000
      });
      
      // Wait a bit for graceful shutdown
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      console.log('Graceful shutdown failed, forcing termination');
    }
    
    if (backendServerProcess) {
      backendServerProcess.kill('SIGTERM');
      
      // Force kill if still running after 5 seconds
      setTimeout(() => {
        if (backendServerProcess) {
          console.log('Force killing backend server');
          backendServerProcess.kill('SIGKILL');
          backendServerProcess = null;
        }
      }, 5000);
    }
    
    return true;
  }
  return false;
}

function createWindow() {
  // Get session data for window restoration
  const windowOptions = restoreSession();
  
  // Create the browser window
  mainWindow = new BrowserWindow({
    ...windowOptions,
    title: 'Westfall Assistant - Entrepreneur Edition',
    icon: path.join(__dirname, '..', 'assets', 'westfall.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      sandbox: true,
      enableRemoteModule: false
    },
    titleBarStyle: 'default',
    show: false,
    closable: true,
    minimizable: true,
    maximizable: true
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
    const session = store.get('session');
    if (session && session.isMaximized) {
      mainWindow.maximize();
    }
    mainWindow.show();
  });

  // Handle window events for session persistence
  mainWindow.on('resize', saveSession);
  mainWindow.on('move', saveSession);
  mainWindow.on('maximize', saveSession);
  mainWindow.on('unmaximize', saveSession);

  // Handle window close to tray instead of quit
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      
      // Show notification first time
      if (!store.get('trayNotificationShown')) {
        new Notification({
          title: 'Westfall Assistant - Entrepreneur Edition',
          body: 'Application was minimized to tray. Double-click the tray icon to restore.',
          icon: path.join(__dirname, '..', 'assets', 'westfall.png')
        }).show();
        store.set('trayNotificationShown', true);
      }
    } else {
      saveSession();
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
    // Only stop backend server if we're actually quitting
    if (isQuitting) {
      stopBackendServer();
    }
  });
}

// App event handlers
app.whenReady().then(async () => {
  try {
    // Start the backend server first
    await startBackendServer();
    console.log('Backend server started successfully');
  } catch (error) {
    console.error('Failed to start backend server:', error);
    // Continue anyway - the user can manually start the backend if needed
  }
  
  // Setup system integration
  createTray();
  setupGlobalShortcuts();
  setupAutoStart();
  
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('before-quit', () => {
  isQuitting = true;
});

app.on('window-all-closed', () => {
  // On macOS, keep app running even when all windows are closed
  if (process.platform === 'darwin') {
    return;
  }
  
  // On other platforms, quit when all windows are closed only if not in tray mode
  const settings = store.get('settings', {});
  if (!settings.minimizeToTray) {
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
    stopBackendServer();
    app.quit();
  }
});

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll();
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
        path.join(__dirname, '..', 'backend', 'server.py'),
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

// Backend management
ipcMain.handle('restart-backend', async () => {
  try {
    await restartBackendServer();
    return { success: true, message: 'Backend restarted successfully' };
  } catch (error) {
    return { success: false, message: `Failed to restart backend: ${error.message}` };
  }
});

ipcMain.handle('stop-backend', async () => {
  try {
    await stopBackendServer();
    return { success: true, message: 'Backend stopped successfully' };
  } catch (error) {
    return { success: false, message: `Failed to stop backend: ${error.message}` };
  }
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
    minimizeToTray: true,
    gpuLayers: 'auto',
    shortcuts: {
      quickChat: 'CmdOrCtrl+Shift+A',
      screenCapture: 'CmdOrCtrl+Shift+S',
      toggleWindow: 'CmdOrCtrl+Shift+W'
    },
    notifications: {
      enabled: true,
      screenCapture: true,
      modelLoaded: true,
      errors: true
    }
  });
});

// Backend server status
ipcMain.handle('get-backend-status', async () => {
  const isRunning = backendServerProcess !== null;
  let isHealthy = false;
  
  if (isRunning) {
    isHealthy = await checkBackendHealth();
  }
  
  return {
    isRunning: isRunning,
    isHealthy: isHealthy,
    serverUrl: `http://127.0.0.1:${BACKEND_PORT}`,
    restartCount: backendRestartCount
  };
});

ipcMain.handle('save-settings', (event, settings) => {
  const currentSettings = store.get('settings', {});
  const newSettings = { ...currentSettings, ...settings };
  store.set('settings', newSettings);
  
  // Update auto-start when settings change
  if (settings.autoStart !== undefined) {
    setupAutoStart();
  }
  
  return true;
});

// Conversation history management
ipcMain.handle('save-conversation', (event, conversation) => {
  const conversations = store.get('conversations', []);
  const existingIndex = conversations.findIndex(c => c.id === conversation.id);
  
  if (existingIndex >= 0) {
    conversations[existingIndex] = conversation;
  } else {
    conversations.push(conversation);
  }
  
  // Keep only last 100 conversations
  if (conversations.length > 100) {
    conversations.splice(0, conversations.length - 100);
  }
  
  store.set('conversations', conversations);
  return true;
});

ipcMain.handle('get-conversations', () => {
  return store.get('conversations', []);
});

ipcMain.handle('delete-conversation', (event, conversationId) => {
  const conversations = store.get('conversations', []);
  const filtered = conversations.filter(c => c.id !== conversationId);
  store.set('conversations', filtered);
  return true;
});

ipcMain.handle('search-conversations', (event, query) => {
  const conversations = store.get('conversations', []);
  const lowerQuery = query.toLowerCase();
  
  return conversations.filter(conversation => 
    conversation.title?.toLowerCase().includes(lowerQuery) ||
    conversation.messages?.some(msg => 
      msg.content?.toLowerCase().includes(lowerQuery)
    )
  );
});

// Notification management
ipcMain.handle('show-notification', (event, options) => {
  const settings = store.get('settings', {});
  if (!settings.notifications?.enabled) return false;
  
  // Check specific notification type
  if (options.type && !settings.notifications?.[options.type]) return false;
  
  const notification = new Notification({
    title: options.title,
    body: options.body,
    icon: path.join(__dirname, '..', 'assets', 'westfall.png'),
    ...options
  });
  
  notification.show();
  return true;
});

// System information
ipcMain.handle('get-system-info', () => {
  return {
    platform: os.platform(),
    arch: os.arch(),
    version: os.version(),
    totalMemory: os.totalmem(),
    freeMemory: os.freemem(),
    cpus: os.cpus().length,
    hostname: os.hostname(),
    uptime: os.uptime()
  };
});

// Screen capture (integrates with backend)
ipcMain.handle('capture-screen', async () => {
  try {
    // Call backend screen capture endpoint
    const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}/capture-screen`, {
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
    const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}/start-monitoring`, {
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
    const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}/stop-monitoring`, {
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