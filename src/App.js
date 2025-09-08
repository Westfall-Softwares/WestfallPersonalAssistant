import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  Grid,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Settings as SettingsIcon,
  ScreenshotMonitor as ScreenshotIcon,
  Psychology as ThinkingIcon
} from '@mui/icons-material';

import ChatInterface from './components/ChatInterface';
import ModelManager from './components/ModelManager';
import SettingsPanel from './components/SettingsPanel';
import ScreenCapture from './components/ScreenCapture';
import ThinkingModeSelector from './components/ThinkingModeSelector';
import TailorPackManager from './components/TailorPackManager';
import BusinessDashboard from './components/BusinessDashboard';

const drawerWidth = 240;

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [modelStatus, setModelStatus] = useState('disconnected');
  const [settings, setSettings] = useState({
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

  useEffect(() => {
    // Load settings on startup
    if (window.electronAPI) {
      window.electronAPI.getSettings().then(setSettings);
    }

    // Listen for IPC events
    if (window.electronAPI) {
      const handleOpenSettings = () => {
        setCurrentView('settings');
      };

      window.electronAPI.ipcRenderer?.on('open-settings', handleOpenSettings);

      return () => {
        window.electronAPI.ipcRenderer?.removeListener('open-settings', handleOpenSettings);
      };
    }
  }, []);

  const menuItems = [
    { id: 'dashboard', label: 'Business Dashboard', icon: <ThinkingIcon /> },
    { id: 'chat', label: 'AI Assistant', icon: <ThinkingIcon /> },
    { id: 'models', label: 'Model Manager', icon: <MemoryIcon /> },
    { id: 'tailorpacks', label: 'Tailor Packs', icon: <SettingsIcon /> },
    { id: 'screen', label: 'Screen Capture', icon: <ScreenshotIcon /> },
    { id: 'settings', label: 'Settings', icon: <SettingsIcon /> }
  ];

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <BusinessDashboard />;
      case 'chat':
        return <ChatInterface thinkingMode={settings.thinkingMode} modelStatus={modelStatus} />;
      case 'models':
        return <ModelManager onStatusChange={setModelStatus} />;
      case 'tailorpacks':
        return <TailorPackManager />;
      case 'screen':
        return <ScreenCapture />;
      case 'settings':
        return <SettingsPanel settings={settings} onSettingsChange={setSettings} />;
      default:
        return <BusinessDashboard />;
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <img 
              src="/westfall.png" 
              alt="Westfall Assistant" 
              style={{ height: 32, width: 32 }}
            />
            <Typography variant="h6" noWrap component="div">
              Westfall Assistant - Entrepreneur Edition
            </Typography>
          </Box>
          <Box sx={{ flexGrow: 1 }} />
          <ThinkingModeSelector 
            mode={settings.thinkingMode}
            onChange={(mode) => setSettings(prev => ({ ...prev, thinkingMode: mode }))}
          />
          <Box sx={{ 
            ml: 2, 
            px: 2, 
            py: 1, 
            borderRadius: 1,
            bgcolor: modelStatus === 'connected' ? 'success.main' : 'error.main'
          }}>
            <Typography variant="body2">
              Model: {modelStatus === 'connected' ? 'Connected' : 'Disconnected'}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.id} disablePadding>
                <ListItemButton 
                  selected={currentView === item.id}
                  onClick={() => setCurrentView(item.id)}
                >
                  <ListItemIcon>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {renderContent()}
      </Box>
    </Box>
  );
}

export default App;