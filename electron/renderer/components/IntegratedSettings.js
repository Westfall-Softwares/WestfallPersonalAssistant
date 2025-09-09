import React, { useState, useEffect } from 'react';
import {
  Box,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Divider,
  IconButton,
  Paper,
  InputAdornment,
  Alert
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Close as CloseIcon,
  Visibility,
  VisibilityOff,
  Check as TestIcon
} from '@mui/icons-material';

const IntegratedSettings = () => {
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [showApiKeys, setShowApiKeys] = useState({});
  const [apiKeys, setApiKeys] = useState({
    openweather: '',
    newsapi: '',
    openai: ''
  });
  const [testStatus, setTestStatus] = useState({});

  useEffect(() => {
    // Add keyboard shortcut listener
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === ',') {
        e.preventDefault();
        toggleSettings();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    // Load settings from localStorage if available
    loadSettings();

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const toggleSettings = () => {
    setSettingsVisible(!settingsVisible);
  };

  const hideSettingsPanel = () => {
    setSettingsVisible(false);
  };

  const loadSettings = () => {
    try {
      const saved = localStorage.getItem('integratedSettings');
      if (saved) {
        const settings = JSON.parse(saved);
        setApiKeys(settings.apiKeys || {});
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveSettings = () => {
    try {
      const settings = {
        apiKeys,
        timestamp: new Date().toISOString()
      };
      localStorage.setItem('integratedSettings', JSON.stringify(settings));
      
      // Show success message
      setTestStatus({
        ...testStatus,
        save: { status: 'success', message: 'Settings saved successfully!' }
      });
      
      // Hide success message after 3 seconds
      setTimeout(() => {
        setTestStatus(prev => ({ ...prev, save: null }));
      }, 3000);
    } catch (error) {
      setTestStatus({
        ...testStatus,
        save: { status: 'error', message: 'Error saving settings' }
      });
    }
  };

  const toggleApiKeyVisibility = (keyType) => {
    setShowApiKeys(prev => ({
      ...prev,
      [keyType]: !prev[keyType]
    }));
  };

  const testKey = async (keyType) => {
    const key = apiKeys[keyType];
    if (!key.trim()) {
      setTestStatus({
        ...testStatus,
        [keyType]: { status: 'warning', message: 'Please enter an API key first' }
      });
      return;
    }

    setTestStatus({
      ...testStatus,
      [keyType]: { status: 'testing', message: 'Testing...' }
    });

    // Simulate API testing (replace with actual API calls)
    setTimeout(() => {
      // For demo purposes, we'll simulate success for non-empty keys
      const isValid = key.length > 10; // Simple validation
      setTestStatus({
        ...testStatus,
        [keyType]: {
          status: isValid ? 'success' : 'error',
          message: isValid ? '✅ Valid' : '❌ Invalid key format'
        }
      });
    }, 1500);
  };

  const handleApiKeyChange = (keyType, value) => {
    setApiKeys(prev => ({
      ...prev,
      [keyType]: value
    }));
    // Clear test status when key changes
    if (testStatus[keyType]) {
      setTestStatus(prev => ({ ...prev, [keyType]: null }));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'success';
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'testing': return 'info';
      default: return 'default';
    }
  };

  return (
    <>
      {/* Floating Settings Button */}
      <Fab
        color="primary"
        aria-label="settings"
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
          boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
        }}
        onClick={toggleSettings}
      >
        <SettingsIcon />
      </Fab>

      {/* Settings Modal */}
      <Dialog
        open={settingsVisible}
        onClose={hideSettingsPanel}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            maxHeight: '80vh'
          }
        }}
      >
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h5">Settings</Typography>
          <IconButton onClick={hideSettingsPanel} edge="end">
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent dividers>
          {/* Save Status Alert */}
          {testStatus.save && (
            <Alert 
              severity={getStatusColor(testStatus.save.status)} 
              sx={{ mb: 2 }}
              onClose={() => setTestStatus(prev => ({ ...prev, save: null }))}
            >
              {testStatus.save.message}
            </Alert>
          )}

          {/* API Keys Section */}
          <Paper elevation={1} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              API Keys
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Configure your API keys for external services
            </Typography>

            {/* OpenWeather API Key */}
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="OpenWeather API Key"
                type={showApiKeys.openweather ? 'text' : 'password'}
                value={apiKeys.openweather}
                onChange={(e) => handleApiKeyChange('openweather', e.target.value)}
                placeholder="Enter your OpenWeather API key"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => toggleApiKeyVisibility('openweather')}
                        edge="end"
                      >
                        {showApiKeys.openweather ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<TestIcon />}
                        onClick={() => testKey('openweather')}
                        sx={{ ml: 1 }}
                        disabled={testStatus.openweather?.status === 'testing'}
                      >
                        Test
                      </Button>
                    </InputAdornment>
                  )
                }}
                sx={{ mb: 1 }}
              />
              {testStatus.openweather && (
                <Alert severity={getStatusColor(testStatus.openweather.status)} size="small">
                  {testStatus.openweather.message}
                </Alert>
              )}
            </Box>

            {/* News API Key */}
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="News API Key"
                type={showApiKeys.newsapi ? 'text' : 'password'}
                value={apiKeys.newsapi}
                onChange={(e) => handleApiKeyChange('newsapi', e.target.value)}
                placeholder="Enter your News API key"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => toggleApiKeyVisibility('newsapi')}
                        edge="end"
                      >
                        {showApiKeys.newsapi ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<TestIcon />}
                        onClick={() => testKey('newsapi')}
                        sx={{ ml: 1 }}
                        disabled={testStatus.newsapi?.status === 'testing'}
                      >
                        Test
                      </Button>
                    </InputAdornment>
                  )
                }}
                sx={{ mb: 1 }}
              />
              {testStatus.newsapi && (
                <Alert severity={getStatusColor(testStatus.newsapi.status)} size="small">
                  {testStatus.newsapi.message}
                </Alert>
              )}
            </Box>

            {/* OpenAI API Key */}
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="OpenAI API Key"
                type={showApiKeys.openai ? 'text' : 'password'}
                value={apiKeys.openai}
                onChange={(e) => handleApiKeyChange('openai', e.target.value)}
                placeholder="Enter your OpenAI API key"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => toggleApiKeyVisibility('openai')}
                        edge="end"
                      >
                        {showApiKeys.openai ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<TestIcon />}
                        onClick={() => testKey('openai')}
                        sx={{ ml: 1 }}
                        disabled={testStatus.openai?.status === 'testing'}
                      >
                        Test
                      </Button>
                    </InputAdornment>
                  )
                }}
                sx={{ mb: 1 }}
              />
              {testStatus.openai && (
                <Alert severity={getStatusColor(testStatus.openai.status)} size="small">
                  {testStatus.openai.message}
                </Alert>
              )}
            </Box>
          </Paper>

          {/* Keyboard Shortcuts Info */}
          <Paper elevation={1} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Keyboard Shortcuts
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Ctrl/Cmd + ,</strong> - Open/close settings panel
            </Typography>
          </Paper>
        </DialogContent>

        <DialogActions>
          <Button onClick={hideSettingsPanel}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            onClick={saveSettings}
            disabled={testStatus.save?.status === 'testing'}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default IntegratedSettings;