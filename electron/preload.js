const { contextBridge } = require('electron');
contextBridge.exposeInMainWorld('api', {
  // In a later step, wire calls to the local backend (127.0.0.1)
});