const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electron', {
  // File system operations
  saveFile: (filename, data) => ipcRenderer.invoke('save-file', filename, data),
  readFile: (filename) => ipcRenderer.invoke('read-file', filename),
  
  // Print functionality
  print: () => ipcRenderer.invoke('print'),
  
  // Database backup
  backupDatabase: () => ipcRenderer.invoke('backup-database'),
  restoreDatabase: (filepath) => ipcRenderer.invoke('restore-database', filepath),
  
  // App info
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  
  // Notifications
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', title, body),
  
  // System info
  getSystemInfo: () => ipcRenderer.invoke('get-system-info')
});