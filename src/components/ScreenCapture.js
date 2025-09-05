import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Divider
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';

const ScreenCapture = () => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [lastCapture, setLastCapture] = useState(null);
  const [error, setError] = useState('');
  const [autoCapture, setAutoCapture] = useState(false);

  const handleCapture = async () => {
    setIsCapturing(true);
    setError('');

    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.captureScreen();
        if (result.success) {
          setLastCapture(result);
        } else {
          setError(result.message || 'Screen capture failed');
        }
      } else {
        setError('Screen capture API not available');
      }
    } catch (error) {
      setError(`Capture error: ${error.message}`);
    } finally {
      setIsCapturing(false);
    }
  };

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Screen Capture & Analysis
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          Capture and analyze screen content for error detection and workflow understanding
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <strong>Privacy Notice:</strong> All screen captures are processed locally. 
          No data is transmitted externally. Screenshots are temporarily stored and securely deleted.
        </Alert>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Capture Controls
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Button
                variant="contained"
                startIcon={<CameraIcon />}
                onClick={handleCapture}
                disabled={isCapturing}
              >
                {isCapturing ? 'Capturing...' : 'Capture Screen'}
              </Button>
              
              {lastCapture && (
                <Button
                  variant="outlined"
                  startIcon={<ViewIcon />}
                  onClick={() => {/* Would open capture viewer */}}
                >
                  View Last Capture
                </Button>
              )}
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={autoCapture}
                  onChange={(e) => setAutoCapture(e.target.checked)}
                />
              }
              label="Continuous monitoring (captures every 30 seconds)"
            />
          </CardContent>
        </Card>

        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Analysis Features
            </Typography>
            
            <Typography variant="body2" gutterBottom>
              <strong>🔍 Text Extraction (OCR):</strong> Extract and analyze text from screenshots
            </Typography>
            <Typography variant="body2" gutterBottom>
              <strong>⚠️ Error Detection:</strong> Identify error messages and crash dialogs
            </Typography>
            <Typography variant="body2" gutterBottom>
              <strong>🖥️ UI State Recognition:</strong> Understand application states and workflows
            </Typography>
            <Typography variant="body2" gutterBottom>
              <strong>🔒 Privacy Masking:</strong> Optional masking of sensitive information
            </Typography>
          </CardContent>
        </Card>

        {lastCapture && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Last Capture Analysis
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Timestamp: {lastCapture.timestamp || 'Not available'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Status: Screen capture functionality is being implemented
              </Typography>
            </CardContent>
          </Card>
        )}

        <Alert severity="warning" sx={{ mt: 3 }}>
          <strong>Implementation Note:</strong> Screen capture functionality requires platform-specific 
          implementations and permission handling. This will be completed in the next development phase.
        </Alert>
      </Paper>
    </Box>
  );
};

export default ScreenCapture;