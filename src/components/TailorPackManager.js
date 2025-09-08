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

  const handleImportPack = () => {
    if (!orderNumber.trim()) {
      setImportError('Please enter an order number');
      return;
    }
    
    // Mock import process
    console.log('Importing pack with order number:', orderNumber);
    setImportDialogOpen(false);
    setOrderNumber('');
    setImportError('');
    
    // Show success message or add to installed packs
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
                <Switch
                  checked={pack.active}
                  onChange={(e) => togglePackActive(pack.id, e.target.checked)}
                  color="primary"
                />
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
                {pack.licenseRequired && (
                  <Chip 
                    label={pack.trialDaysLeft ? `Trial: ${pack.trialDaysLeft} days` : 'Licensed'} 
                    size="small" 
                    color={pack.trialDaysLeft ? 'warning' : 'success'}
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
              
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button
                  size="small"
                  startIcon={<SettingsIcon />}
                  variant="outlined"
                >
                  Configure
                </Button>
                {pack.licenseRequired && pack.trialDaysLeft && (
                  <Button
                    size="small"
                    color="warning"
                    variant="contained"
                  >
                    Upgrade License
                  </Button>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
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
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          📦 Tailor Pack Manager
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setImportDialogOpen(true)}
        >
          Import Pack
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Tailor Packs</strong> are specialized business functionality modules that extend your assistant with industry-specific tools and workflows. 
          Install packs to add features like advanced CRM, marketing automation, financial planning, and more.
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
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Enter your order number or license key to import and activate a Tailor Pack.
          </Typography>
          <TextField
            fullWidth
            label="Order Number / License Key"
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            error={!!importError}
            helperText={importError}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleImportPack} variant="contained">Import Pack</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}