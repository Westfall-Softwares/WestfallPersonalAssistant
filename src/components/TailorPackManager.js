import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Switch,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Divider
} from '@mui/material';
import {
  Extension as ExtensionIcon,
  Business as BusinessIcon,
  Download as DownloadIcon,
  Settings as SettingsIcon,
  Star as StarIcon,
  Add as AddIcon
} from '@mui/icons-material';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tailor-pack-tabpanel-${index}`}
      aria-labelledby={`tailor-pack-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function TailorPackManager() {
  const [currentTab, setCurrentTab] = useState(0);
  const [installedPacks, setInstalledPacks] = useState([]);
  const [availablePacks, setAvailablePacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [orderNumber, setOrderNumber] = useState('');
  const [importError, setImportError] = useState('');
  const [dragOver, setDragOver] = useState(false);

  useEffect(() => {
    loadTailorPacks();
  }, []);

  const loadTailorPacks = async () => {
    setLoading(true);
    try {
      // Mock data for now - replace with actual API calls
      const installed = [
        {
          id: 'marketing-essentials',
          name: 'Marketing Essentials',
          version: '1.2.0',
          description: 'Essential marketing tools for entrepreneurs',
          category: 'marketing',
          active: true,
          features: ['Campaign Tracking', 'Social Media Management', 'Lead Generation'],
          author: 'Westfall Business Tools',
          licenseRequired: false
        },
        {
          id: 'sales-pipeline-pro',
          name: 'Sales Pipeline Pro',
          version: '2.1.0',
          description: 'Advanced sales pipeline management and CRM tools',
          category: 'sales',
          active: false,
          features: ['Advanced CRM', 'Deal Tracking', 'Sales Analytics'],
          author: 'Westfall Business Tools',
          licenseRequired: true,
          trialDaysLeft: 15
        }
      ];

      const available = [
        {
          id: 'finance-master',
          name: 'Finance Master',
          version: '1.0.0',
          description: 'Complete financial management suite for small businesses',
          category: 'finance',
          price: '$29.99/month',
          rating: 4.8,
          features: ['Advanced Accounting', 'Tax Preparation', 'Financial Planning'],
          author: 'Westfall Business Tools'
        },
        {
          id: 'legal-essentials',
          name: 'Legal Essentials',
          version: '1.1.0',
          description: 'Legal document templates and compliance tools',
          category: 'legal',
          price: '$19.99/month',
          rating: 4.6,
          features: ['Contract Templates', 'Compliance Tracking', 'Legal Advice'],
          author: 'Westfall Legal Solutions'
        }
      ];

      setInstalledPacks(installed);
      setAvailablePacks(available);
    } catch (error) {
      console.error('Error loading Tailor Packs:', error);
    } finally {
      setLoading(false);
    }
  };

  const togglePackActive = (packId, active) => {
    setInstalledPacks(packs =>
      packs.map(pack =>
        pack.id === packId ? { ...pack, active } : pack
      )
    );
  };

  const handleImportPack = async () => {
    if (!orderNumber.trim()) {
      setImportError('Please enter an order number');
      return;
    }
    
    setImportError('');
    
    try {
      // Call backend to import pack with order verification
      const response = await fetch('/api/tailor-packs/import', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          orderNumber: orderNumber.trim(),
          verifyLicense: true
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Add to installed packs
        setInstalledPacks(packs => [...packs, result.pack]);
        setImportDialogOpen(false);
        setOrderNumber('');
        
        // Show success notification
        alert(`Successfully imported ${result.pack.name}!`);
      } else {
        setImportError(result.error || 'Failed to import pack');
      }
    } catch (error) {
      setImportError('Network error occurred. Please try again.');
      console.error('Import error:', error);
    }
  };

  const handleImportFromFile = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.zip')) {
      setImportError('Please select a ZIP file');
      return;
    }
    
    const formData = new FormData();
    formData.append('packFile', file);
    
    try {
      const response = await fetch('/api/tailor-packs/import-file', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        setInstalledPacks(packs => [...packs, result.pack]);
        alert(`Successfully imported ${result.pack.name} from file!`);
      } else {
        setImportError(result.error || 'Failed to import pack from file');
      }
    } catch (error) {
      setImportError('File import failed. Please check the file and try again.');
      console.error('File import error:', error);
    }
    
    // Reset file input
    event.target.value = '';
  };

  const handleExportPack = async (packId) => {
    try {
      const response = await fetch(`/api/tailor-packs/export/${packId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${packId}-export.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const result = await response.json();
        alert(`Export failed: ${result.error}`);
      }
    } catch (error) {
      alert('Export failed. Please try again.');
      console.error('Export error:', error);
    }
  };

  // Enhanced drag-and-drop functionality for entrepreneur workflow
  const handleDragOver = (event) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragOver(false);
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setDragOver(false);
    
    const files = Array.from(event.dataTransfer.files);
    const zipFiles = files.filter(file => file.name.endsWith('.zip'));
    
    if (zipFiles.length === 0) {
      setImportError('Please drop ZIP files containing Tailor Packs');
      return;
    }
    
    // Process the first ZIP file
    const file = zipFiles[0];
    await processFileImport(file);
  };

  const processFileImport = async (file) => {
    const formData = new FormData();
    formData.append('packFile', file);
    
    try {
      const response = await fetch('/api/tailor-packs/import-file', {
        method: 'POST',
        body: formData
      });
      
      const result = await response.json();
      
      if (result.success) {
        setInstalledPacks(packs => [...packs, result.pack]);
        alert(`🚀 Successfully imported ${result.pack.name}! Your business assistant just got more powerful.`);
      } else {
        setImportError(result.error || 'Failed to import pack from file');
      }
    } catch (error) {
      setImportError('File import failed. Please check the file and try again.');
      console.error('File import error:', error);
    }
  };

  const handleBackupAllPacks = async () => {
    try {
      const response = await fetch('/api/tailor-packs/backup', {
        method: 'POST'
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tailor-packs-backup-${new Date().toISOString().split('T')[0]}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('Backup created successfully!');
      } else {
        const result = await response.json();
        alert(`Backup failed: ${result.error}`);
      }
    } catch (error) {
      alert('Backup failed. Please try again.');
      console.error('Backup error:', error);
    }
  };

  const renderInstalledPacks = () => (
    <Grid container spacing={3}>
      {installedPacks.map((pack) => (
        <Grid item xs={12} md={6} key={pack.id}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="h6" component="h3">
                    {pack.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    v{pack.version} • {pack.author}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Switch
                    checked={pack.active}
                    onChange={(e) => togglePackActive(pack.id, e.target.checked)}
                    color="primary"
                  />
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => handleExportPack(pack.id)}
                    title="Export pack"
                  >
                    Export
                  </Button>
                </Box>
              </Box>
              
              <Typography variant="body2" sx={{ mb: 2 }}>
                {pack.description}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                <Chip 
                  label={pack.category} 
                  size="small" 
                  color="primary" 
                  variant="outlined"
                />
                {pack.targetAudience && (
                  <Chip 
                    label={pack.targetAudience} 
                    size="small" 
                    color="secondary" 
                    variant="outlined"
                  />
                )}
                {pack.licenseRequired && (
                  <Chip 
                    label={pack.trialDaysLeft ? `Trial: ${pack.trialDaysLeft} days` : 'Licensed'} 
                    size="small" 
                    color={pack.trialDaysLeft ? 'warning' : 'success'}
                  />
                )}
                {pack.dependencies && pack.dependencies.length > 0 && (
                  <Chip 
                    label={`${pack.dependencies.length} dependencies`} 
                    size="small" 
                    color="info" 
                    variant="outlined"
                    title={`Dependencies: ${pack.dependencies.join(', ')}`}
                  />
                )}
              </Box>
              
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Features:
              </Typography>
              <List dense>
                {pack.features.map((feature, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemText 
                      primary={feature} 
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
              
              {/* Pack Actions */}
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button size="small" variant="text">
                  Settings
                </Button>
                <Button size="small" variant="text" color="error">
                  Uninstall
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
      
      {installedPacks.length === 0 && (
        <Grid item xs={12}>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <ExtensionIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Tailor Packs Installed
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Install your first Tailor Pack to extend your business capabilities
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
              onClick={() => setImportDialogOpen(true)}
            >
              Import Your First Pack
            </Button>
          </Box>
        </Grid>
      )}
    </Grid>
  );

  const renderAvailablePacks = () => (
    <Grid container spacing={3}>
      {availablePacks.map((pack) => (
        <Grid item xs={12} md={6} key={pack.id}>
          <Card elevation={2}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="h6" component="h3">
                    {pack.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    v{pack.version} • {pack.author}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <StarIcon sx={{ color: 'gold', fontSize: 16 }} />
                  <Typography variant="body2">{pack.rating}</Typography>
                </Box>
              </Box>
              
              <Typography variant="body2" sx={{ mb: 2 }}>
                {pack.description}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                <Chip 
                  label={pack.category} 
                  size="small" 
                  color="primary" 
                  variant="outlined"
                />
                <Chip 
                  label={pack.price} 
                  size="small" 
                  color="success"
                />
              </Box>
              
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Features:
              </Typography>
              <List dense>
                {pack.features.map((feature, index) => (
                  <ListItem key={index} sx={{ py: 0 }}>
                    <ListItemText 
                      primary={feature}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
              
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  startIcon={<DownloadIcon />}
                  variant="contained"
                  color="primary"
                >
                  Start Trial
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                >
                  Learn More
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box 
      sx={{ width: '100%' }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ color: '#1976d2', fontWeight: 'bold' }}>
          🚀 Business Extension Manager
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={<AddIcon />}
          onClick={() => setImportDialogOpen(true)}
          sx={{ 
            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
            boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
          }}
        >
          Add Business Pack
        </Button>
      </Box>

      {dragOver && (
        <Card sx={{ 
          mb: 3, 
          p: 4, 
          textAlign: 'center', 
          backgroundColor: '#e3f2fd',
          border: '2px dashed #2196f3'
        }}>
          <Typography variant="h6" color="primary">
            📦 Drop your Tailor Pack ZIP file here to install
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Drag and drop makes installing business functionality fast and easy
          </Typography>
        </Card>
      )}

      <Alert severity="info" sx={{ mb: 3, backgroundColor: '#f8f9fa' }}>
        <Typography variant="body2">
          <strong>🎯 Business Tailor Packs</strong> are specialized functionality modules designed for entrepreneurs and small businesses. 
          Each pack adds industry-specific tools, automations, and workflows to supercharge your business operations.
          <br />
          <strong>💡 Pro Tip:</strong> Start with Marketing Essentials or Sales Pipeline Pro for immediate productivity gains.
        </Typography>
      </Alert>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)}>
          <Tab label={`Installed (${installedPacks.length})`} />
          <Tab label={`Available (${availablePacks.length})`} />
          <Tab label="Settings" />
        </Tabs>
      </Box>

      <TabPanel value={currentTab} index={0}>
        {installedPacks.length > 0 ? (
          renderInstalledPacks()
        ) : (
          <Box textAlign="center" py={4}>
            <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Tailor Packs Installed
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Browse available packs to extend your business assistant with specialized tools.
            </Typography>
            <Button
              variant="contained"
              onClick={() => setCurrentTab(1)}
            >
              Browse Available Packs
            </Button>
          </Box>
        )}
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        {renderAvailablePacks()}
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Tailor Pack Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Auto-update Settings
            </Typography>
            <List>
              <ListItem>
                <ListItemText primary="Auto-update packs" secondary="Automatically download and install pack updates" />
                <ListItemSecondaryAction>
                  <Switch defaultChecked />
                </ListItemSecondaryAction>
              </ListItem>
              <ListItem>
                <ListItemText primary="Check for updates daily" secondary="Check for pack updates every day" />
                <ListItemSecondaryAction>
                  <Switch defaultChecked />
                </ListItemSecondaryAction>
              </ListItem>
            </List>
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="subtitle2" gutterBottom>
              Pack Storage
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Packs are stored in: ~/.config/westfall-assistant/tailor_packs/
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              <Button variant="outlined" sx={{ mr: 2 }}>
                Open Pack Directory
              </Button>
              <Button variant="outlined" color="warning">
                Clear Pack Cache
              </Button>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Import Pack Dialog */}
      <Dialog open={importDialogOpen} onClose={() => setImportDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Import Tailor Pack</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Method 1: License/Order Number
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Enter your order number or license key to download and import a Tailor Pack.
          </Typography>
          <TextField
            fullWidth
            label="Order Number / License Key"
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            error={!!importError}
            helperText={importError}
            sx={{ mt: 1, mb: 2 }}
          />
          <Button 
            onClick={handleImportPack} 
            variant="contained" 
            disabled={!orderNumber.trim()}
            fullWidth
            sx={{ mb: 3 }}
          >
            Import from License
          </Button>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Method 2: Upload Pack File
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Upload a Tailor Pack ZIP file directly.
          </Typography>
          <input
            accept=".zip"
            style={{ display: 'none' }}
            id="pack-file-input"
            type="file"
            onChange={handleImportFromFile}
          />
          <label htmlFor="pack-file-input">
            <Button 
              variant="outlined" 
              component="span" 
              fullWidth
              startIcon={<DownloadIcon />}
            >
              Select Pack File (.zip)
            </Button>
          </label>
          
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Backup & Restore
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button 
              variant="outlined" 
              onClick={handleBackupAllPacks}
              fullWidth
            >
              Backup All Packs
            </Button>
            <input
              accept=".zip"
              style={{ display: 'none' }}
              id="restore-backup-input"
              type="file"
              onChange={(e) => {
                // Handle restore from backup
                console.log('Restore backup:', e.target.files[0]);
              }}
            />
            <label htmlFor="restore-backup-input">
              <Button 
                variant="outlined" 
                component="span"
                fullWidth
              >
                Restore Backup
              </Button>
            </label>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setImportDialogOpen(false);
            setImportError('');
            setOrderNumber('');
          }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}