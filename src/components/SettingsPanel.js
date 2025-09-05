import React from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Slider,
  Card,
  CardContent,
  Divider,
  Button
} from '@mui/material';
import {
  Save as SaveIcon,
  Restore as RestoreIcon
} from '@mui/icons-material';

const SettingsPanel = ({ settings, onSettingsChange }) => {
  const handleSettingChange = (key, value) => {
    const newSettings = { ...settings, [key]: value };
    onSettingsChange(newSettings);
    
    // Save to electron store
    if (window.electronAPI) {
      window.electronAPI.saveSettings(newSettings);
    }
  };

  const handleReset = () => {
    const defaultSettings = {
      thinkingMode: 'normal',
      theme: 'dark',
      autoStart: false,
      gpuLayers: 'auto'
    };
    onSettingsChange(defaultSettings);
    if (window.electronAPI) {
      window.electronAPI.saveSettings(defaultSettings);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Settings
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          Configure your personal assistant preferences
        </Typography>

        {/* UI Settings */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              User Interface
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Default Thinking Mode</InputLabel>
              <Select
                value={settings.thinkingMode}
                onChange={(e) => handleSettingChange('thinkingMode', e.target.value)}
                label="Default Thinking Mode"
              >
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="thinking">Thinking</MenuItem>
                <MenuItem value="research">Research Grade</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Theme</InputLabel>
              <Select
                value={settings.theme}
                onChange={(e) => handleSettingChange('theme', e.target.value)}
                label="Theme"
              >
                <MenuItem value="dark">Dark</MenuItem>
                <MenuItem value="light">Light</MenuItem>
                <MenuItem value="auto">Auto (System)</MenuItem>
              </Select>
            </FormControl>
          </CardContent>
        </Card>

        {/* System Settings */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Integration
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={settings.autoStart}
                  onChange={(e) => handleSettingChange('autoStart', e.target.checked)}
                />
              }
              label="Start with Windows"
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.systemTray || false}
                  onChange={(e) => handleSettingChange('systemTray', e.target.checked)}
                />
              }
              label="Minimize to system tray"
              sx={{ mb: 2 }}
            />
          </CardContent>
        </Card>

        {/* GPU Settings */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              GPU Acceleration
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>GPU Layer Offloading</InputLabel>
              <Select
                value={settings.gpuLayers}
                onChange={(e) => handleSettingChange('gpuLayers', e.target.value)}
                label="GPU Layer Offloading"
              >
                <MenuItem value="auto">Auto (Recommended for RTX 2060)</MenuItem>
                <MenuItem value="0">CPU Only</MenuItem>
                <MenuItem value="10">Conservative (10 layers)</MenuItem>
                <MenuItem value="20">Balanced (20 layers)</MenuItem>
                <MenuItem value="30">Aggressive (30 layers)</MenuItem>
                <MenuItem value="max">Maximum</MenuItem>
              </Select>
            </FormControl>

            <Typography variant="body2" color="textSecondary" gutterBottom>
              VRAM Usage Limit
            </Typography>
            <Slider
              value={settings.vramLimit || 80}
              onChange={(e, value) => handleSettingChange('vramLimit', value)}
              min={50}
              max={95}
              step={5}
              marks={[
                { value: 50, label: '50%' },
                { value: 70, label: '70%' },
                { value: 80, label: '80%' },
                { value: 90, label: '90%' },
                { value: 95, label: '95%' }
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={(value) => `${value}%`}
            />
            <Typography variant="caption" color="textSecondary">
              Recommended: 80% for RTX 2060 (leaves room for other applications)
            </Typography>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Privacy & Security
            </Typography>

            <FormControlLabel
              control={
                <Switch
                  checked={settings.localProcessing || true}
                  onChange={(e) => handleSettingChange('localProcessing', e.target.checked)}
                />
              }
              label="Local processing only (no external connections)"
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.conversationHistory || true}
                  onChange={(e) => handleSettingChange('conversationHistory', e.target.checked)}
                />
              }
              label="Save conversation history"
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.screenCaptureMasking || false}
                  onChange={(e) => handleSettingChange('screenCaptureMasking', e.target.checked)}
                />
              }
              label="Auto-mask sensitive information in screenshots"
            />
          </CardContent>
        </Card>

        {/* Actions */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={() => {
              if (window.electronAPI) {
                window.electronAPI.saveSettings(settings);
              }
            }}
          >
            Save Settings
          </Button>
          <Button
            variant="outlined"
            startIcon={<RestoreIcon />}
            onClick={handleReset}
          >
            Reset to Defaults
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SettingsPanel;