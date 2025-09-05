import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  FolderOpen as FolderIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';

const ModelManager = ({ onStatusChange }) => {
  const [selectedModel, setSelectedModel] = useState('');
  const [lastModel, setLastModel] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverStatus, setServerStatus] = useState('stopped');
  const [gpuInfo, setGpuInfo] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    // Load last used model and GPU info
    loadInitialData();
  }, []);

  useEffect(() => {
    // Update parent component with status
    onStatusChange(serverStatus === 'running' ? 'connected' : 'disconnected');
  }, [serverStatus, onStatusChange]);

  const loadInitialData = async () => {
    if (window.electronAPI) {
      try {
        const lastModelPath = await window.electronAPI.getLastModel();
        const gpu = await window.electronAPI.getGPUInfo();
        
        if (lastModelPath) {
          setLastModel(lastModelPath);
          setSelectedModel(lastModelPath);
        }
        setGpuInfo(gpu);
      } catch (error) {
        console.error('Error loading initial data:', error);
      }
    }
  };

  const handleSelectModel = async () => {
    if (window.electronAPI) {
      try {
        const modelPath = await window.electronAPI.selectModelFile();
        if (modelPath) {
          setSelectedModel(modelPath);
          setError('');
        }
      } catch (error) {
        setError('Failed to select model file');
        console.error('Error selecting model:', error);
      }
    }
  };

  const handleStartServer = async () => {
    if (!selectedModel) {
      setError('Please select a model first');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      if (window.electronAPI) {
        await window.electronAPI.startModelServer(selectedModel);
        setServerStatus('running');
      }
    } catch (error) {
      setError(`Failed to start model server: ${error.message}`);
      setServerStatus('stopped');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopServer = async () => {
    setIsLoading(true);
    try {
      if (window.electronAPI) {
        await window.electronAPI.stopModelServer();
        setServerStatus('stopped');
      }
    } catch (error) {
      setError(`Failed to stop model server: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getModelName = (path) => {
    if (!path) return 'No model selected';
    return path.split(/[\\\/]/).pop();
  };

  const getStatusColor = () => {
    switch (serverStatus) {
      case 'running': return 'success';
      case 'starting': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Model Management
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          Select and manage local AI models for the assistant
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Model Selection */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Model Selection
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <TextField
                    fullWidth
                    label="Selected Model"
                    value={getModelName(selectedModel)}
                    InputProps={{
                      readOnly: true,
                    }}
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<FolderIcon />}
                    onClick={handleSelectModel}
                    sx={{ mr: 1 }}
                  >
                    Browse Models
                  </Button>
                </Box>

                {lastModel && lastModel !== selectedModel && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Last used model:
                    </Typography>
                    <Chip 
                      label={getModelName(lastModel)}
                      onClick={() => setSelectedModel(lastModel)}
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                )}

                <Divider sx={{ my: 2 }} />

                {/* Server Controls */}
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Button
                    variant="contained"
                    startIcon={<StartIcon />}
                    onClick={handleStartServer}
                    disabled={!selectedModel || serverStatus === 'running' || isLoading}
                    color="success"
                  >
                    Start Model
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<StopIcon />}
                    onClick={handleStopServer}
                    disabled={serverStatus !== 'running' || isLoading}
                    color="error"
                  >
                    Stop Model
                  </Button>
                  <Chip 
                    label={serverStatus.charAt(0).toUpperCase() + serverStatus.slice(1)}
                    color={getStatusColor()}
                    size="small"
                  />
                </Box>

                {isLoading && (
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress />
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      {serverStatus === 'running' ? 'Stopping server...' : 'Starting server...'}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* GPU Information */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <MemoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  GPU Information
                </Typography>
                
                {gpuInfo ? (
                  <Box>
                    <Typography variant="body2" gutterBottom>
                      <strong>GPU:</strong> {gpuInfo.gpuName}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Total VRAM:</strong> {gpuInfo.vramTotal}
                    </Typography>
                    <Typography variant="body2" gutterBottom>
                      <strong>Available:</strong> {gpuInfo.vramAvailable}
                    </Typography>
                    <Chip 
                      label={gpuInfo.hasGPU ? 'GPU Available' : 'No GPU'}
                      color={gpuInfo.hasGPU ? 'success' : 'default'}
                      size="small"
                      sx={{ mt: 1 }}
                    />
                  </Box>
                ) : (
                  <Typography variant="body2" color="textSecondary">
                    Loading GPU information...
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Supported Formats */}
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Supported Model Formats
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {['GGUF', 'GGML', 'PyTorch (.pt, .pth)', 'SafeTensors', 'Binary (.bin)'].map((format) => (
                <Chip key={format} label={format} variant="outlined" size="small" />
              ))}
            </Box>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
              Select quantized models (Q4, Q5, Q8) for optimal performance with RTX 2060.
            </Typography>
          </CardContent>
        </Card>
      </Paper>
    </Box>
  );
};

export default ModelManager;