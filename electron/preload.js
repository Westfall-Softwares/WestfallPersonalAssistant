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
  
  // Backend server status and management
  getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  stopBackend: () => ipcRenderer.invoke('stop-backend'),
  
  // Screen capture
  captureScreen: () => ipcRenderer.invoke('capture-screen'),
  startMonitoring: (interval) => ipcRenderer.invoke('start-monitoring', interval),
  stopMonitoring: () => ipcRenderer.invoke('stop-monitoring'),
  
  // Conversation management
  saveConversation: (conversation) => ipcRenderer.invoke('save-conversation', conversation),
  getConversations: () => ipcRenderer.invoke('get-conversations'),
  deleteConversation: (conversationId) => ipcRenderer.invoke('delete-conversation', conversationId),
  searchConversations: (query) => ipcRenderer.invoke('search-conversations', query),
  
  // Notifications
  showNotification: (options) => ipcRenderer.invoke('show-notification', options),
  
  // System information
  getSystemInfo: () => ipcRenderer.invoke('get-system-info'),
  
  // Backend communication
  sendMessage: (message) => ipcRenderer.invoke('send-message', message),
  
  // IPC Renderer for event listeners (limited exposure)
  ipcRenderer: {
    on: (channel, callback) => {
      const validChannels = ['focus-chat', 'open-settings', 'backend-message', 'backend-error'];
      if (validChannels.includes(channel)) {
        ipcRenderer.on(channel, callback);
      }
    },
    removeListener: (channel, callback) => {
      const validChannels = ['focus-chat', 'open-settings', 'backend-message', 'backend-error'];
      if (validChannels.includes(channel)) {
        ipcRenderer.removeListener(channel, callback);
      }
    }
  }
});