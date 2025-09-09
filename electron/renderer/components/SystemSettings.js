import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Switch,
  FormControlLabel,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Button,
  Chip,
  Alert,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  Grid,
  IconButton,
  Tooltip,
  Paper
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Computer as ComputerIcon,
  Keyboard as KeyboardIcon,
  Security as SecurityIcon,
  Save as SaveIcon,
  Restore as RestoreIcon,
  Info as InfoIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

const ipcRenderer = window.electronAPI?.ipcRenderer;

function SystemSettings({ settings, onSettingsChange }) {
  const [localSettings, setLocalSettings] = useState(settings);
  const [systemInfo, setSystemInfo] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const info = await ipcRenderer.invoke('get-system-info');
      setSystemInfo(info);
    } catch (error) {
      console.error('Failed to load system info:', error);
    }
  };

  const handleSettingChange = (key, value) => {
    const newSettings = { ...localSettings };
    if (key.includes('.')) {
      const [parent, child] = key.split('.');
      if (!newSettings[parent]) newSettings[parent] = {};
      newSettings[parent][child] = value;
    } else {
      newSettings[key] = value;
    }
    
    setLocalSettings(newSettings);
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      await ipcRenderer.invoke('save-settings', localSettings);
      onSettingsChange(localSettings);
      setHasChanges(false);
      
      // Show notification
      await ipcRenderer.invoke('show-notification', {
        title: 'Settings Saved',
        body: 'Your system settings have been saved successfully.',
        type: 'info'
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleReset = () => {
    setLocalSettings(settings);
    setHasChanges(false);
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <SettingsIcon />
        <Typography variant="h5">System Settings</Typography>
        {hasChanges && (
          <Chip label="Unsaved Changes" color="warning" size="small" />
        )}
      </Box>

      {/* System Integration */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <ComputerIcon />
            <Typography variant="h6">System Integration</Typography>
          </Box>
          
          <List>
            <ListItem>
              <ListItemText
                primary="Auto-start with System"
                secondary="Automatically start the assistant when your computer starts"
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={localSettings.autoStart || false}
                  onChange={(e) => handleSettingChange('autoStart', e.target.checked)}
                />
              </ListItemSecondaryAction>
            </ListItem>
            
            <ListItem>
              <ListItemText
                primary="Minimize to System Tray"
                secondary="Keep the assistant running in the background when closed"
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={localSettings.minimizeToTray !== false}
                  onChange={(e) => handleSettingChange('minimizeToTray', e.target.checked)}
                />
              </ListItemSecondaryAction>
            </ListItem>
          </List>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <NotificationsIcon />
            <Typography variant="h6">Notifications</Typography>
          </Box>
          
          <List>
            <ListItem>
              <ListItemText
                primary="Enable Notifications"
                secondary="Show system notifications for important events"
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={localSettings.notifications?.enabled !== false}
                  onChange={(e) => handleSettingChange('notifications.enabled', e.target.checked)}
                />
              </ListItemSecondaryAction>
            </ListItem>
            
            <ListItem disabled={!localSettings.notifications?.enabled}>
              <ListItemText
                primary="Screen Capture Notifications"
                secondary="Notify when screen captures are completed"
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={localSettings.notifications?.screenCapture !== false}
                  onChange={(e) => handleSettingChange('notifications.screenCapture', e.target.checked)}
                />
              </ListItemSecondaryAction>
            </ListItem>
            
            <ListItem disabled={!localSettings.notifications?.enabled}>
              <ListItemText
                primary="Model Loading Notifications"
                secondary="Notify when AI models are loaded or unloaded"
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={localSettings.notifications?.modelLoaded !== false}
                  onChange={(e) => handleSettingChange('notifications.modelLoaded', e.target.checked)}
                />
              </ListItemSecondaryAction>
            </ListItem>
            
            <ListItem disabled={!localSettings.notifications?.enabled}>
              <ListItemText
                primary="Error Notifications"
                secondary="Show notifications for errors and important warnings"
              />
              <ListItemSecondaryAction>
                <Switch
                  checked={localSettings.notifications?.errors !== false}
                  onChange={(e) => handleSettingChange('notifications.errors', e.target.checked)}
                />
              </ListItemSecondaryAction>
            </ListItem>
          </List>
        </CardContent>
      </Card>

      {/* Keyboard Shortcuts */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <KeyboardIcon />
            <Typography variant="h6">Keyboard Shortcuts</Typography>
          </Box>
          
          <Alert severity="info" sx={{ mb: 2 }}>
            Global shortcuts work even when the application is minimized to the system tray.
          </Alert>
          
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Quick Chat"
                value={localSettings.shortcuts?.quickChat || 'CmdOrCtrl+Shift+A'}
                disabled
                helperText="Opens chat interface quickly"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Screen Capture"
                value={localSettings.shortcuts?.screenCapture || 'CmdOrCtrl+Shift+S'}
                disabled
                helperText="Captures screen instantly"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Toggle Window"
                value={localSettings.shortcuts?.toggleWindow || 'CmdOrCtrl+Shift+W'}
                disabled
                helperText="Show/hide main window"
              />
            </Grid>
          </Grid>
          
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Keyboard shortcuts are currently fixed but will be customizable in a future update.
          </Typography>
        </CardContent>
      </Card>

      {/* System Information */}
      {systemInfo && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <InfoIcon />
              <Typography variant="h6">System Information</Typography>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">Platform</Typography>
                  <Typography variant="body1">{systemInfo.platform} ({systemInfo.arch})</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">CPU Cores</Typography>
                  <Typography variant="body1">{systemInfo.cpus}</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">Total Memory</Typography>
                  <Typography variant="body1">{formatBytes(systemInfo.totalMemory)}</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">Free Memory</Typography>
                  <Typography variant="body1">{formatBytes(systemInfo.freeMemory)}</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">Hostname</Typography>
                  <Typography variant="body1">{systemInfo.hostname}</Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary">System Uptime</Typography>
                  <Typography variant="body1">
                    {Math.floor(systemInfo.uptime / 3600)} hours
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<RestoreIcon />}
          onClick={handleReset}
          disabled={!hasChanges}
        >
          Reset Changes
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={!hasChanges}
        >
          Save Settings
        </Button>
      </Box>
    </Box>
  );
}

export default SystemSettings;