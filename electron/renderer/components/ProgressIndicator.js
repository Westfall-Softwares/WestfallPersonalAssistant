import React from 'react';
import {
  Box,
  CircularProgress,
  LinearProgress,
  Typography,
  Fade
} from '@mui/material';

/**
 * Progress indicator component for showing operation progress
 */
export default function ProgressIndicator({ 
  type = 'circular', 
  progress = 0, 
  message = '', 
  visible = true,
  size = 40,
  color = 'primary' 
}) {
  if (!visible) return null;

  return (
    <Fade in={visible}>
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: type === 'linear' ? 'column' : 'row',
          alignItems: 'center', 
          gap: 2,
          p: 2
        }}
      >
        {type === 'circular' ? (
          <CircularProgress 
            size={size} 
            color={color}
            variant={progress > 0 ? 'determinate' : 'indeterminate'}
            value={progress * 100}
          />
        ) : (
          <Box sx={{ width: '100%' }}>
            <LinearProgress 
              color={color}
              variant={progress > 0 ? 'determinate' : 'indeterminate'}
              value={progress * 100}
            />
          </Box>
        )}
        
        {message && (
          <Typography variant="body2" color="text.secondary">
            {message}
            {progress > 0 && ` (${Math.round(progress * 100)}%)`}
          </Typography>
        )}
      </Box>
    </Fade>
  );
}

/**
 * Spinner component for quick loading states
 */
export function Spinner({ size = 24, color = 'primary', message = '' }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <CircularProgress size={size} color={color} />
      {message && (
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
      )}
    </Box>
  );
}

/**
 * Progress bar component for linear progress
 */
export function ProgressBar({ progress = 0, message = '', color = 'primary' }) {
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {message}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {Math.round(progress * 100)}%
        </Typography>
      </Box>
      <LinearProgress 
        variant="determinate" 
        value={progress * 100} 
        color={color}
        sx={{ height: 8, borderRadius: 4 }}
      />
    </Box>
  );
}