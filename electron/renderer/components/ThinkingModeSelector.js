import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip
} from '@mui/material';

const ThinkingModeSelector = ({ mode, onChange }) => {
  const modes = [
    { 
      value: 'normal', 
      label: 'Normal', 
      description: 'Standard responses',
      color: 'default'
    },
    { 
      value: 'thinking', 
      label: 'Thinking', 
      description: 'Shows reasoning process',
      color: 'primary'
    },
    { 
      value: 'research', 
      label: 'Research', 
      description: 'Deep analysis with citations',
      color: 'secondary'
    }
  ];

  const currentMode = modes.find(m => m.value === mode) || modes[0];

  return (
    <FormControl size="small" sx={{ minWidth: 120 }}>
      <InputLabel>Thinking Mode</InputLabel>
      <Select
        value={mode}
        onChange={(e) => onChange(e.target.value)}
        label="Thinking Mode"
      >
        {modes.map((modeOption) => (
          <MenuItem key={modeOption.value} value={modeOption.value}>
            <Chip 
              label={modeOption.label}
              color={modeOption.color}
              size="small"
              sx={{ mr: 1 }}
            />
            {modeOption.description}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default ThinkingModeSelector;