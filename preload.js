const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Model management
  selectModelFile: () => ipcRenderer.invoke('select-model-file'),
  getLastModel: () => ipcRenderer.invoke('get-last-model'),
  startModelServer: (modelPath) => ipcRenderer.invoke('start-model-server', modelPath),
  stopModelServer: () => ipcRenderer.invoke('stop-model-server'),
  
  // GPU information
  getGPUInfo: () => ipcRenderer.invoke('get-gpu-info'),
  
  // Settings
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  
  // Screen capture
  captureScreen: () => ipcRenderer.invoke('capture-screen'),
  
  // Backend communication
  sendMessage: (message) => ipcRenderer.invoke('send-message', message),
  
  // Event listeners
  onBackendMessage: (callback) => ipcRenderer.on('backend-message', callback),
  removeBackendMessage: (callback) => ipcRenderer.removeListener('backend-message', callback)
});