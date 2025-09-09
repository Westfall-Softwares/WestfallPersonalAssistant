import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Chip,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Checkbox,
  Paper,
  Divider
} from '@mui/material';
import {
  Business as BusinessIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Extension as ExtensionIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';

const steps = [
  'Business Profile',
  'Business Goals',
  'Connect Calendar',
  'Tool Selection',
  'Configuration',
  'Complete Setup'
];

export default function BusinessSetupWizard({ onComplete, onSkip }) {
  const [activeStep, setActiveStep] = useState(0);
  const [businessProfile, setBusinessProfile] = useState({
    businessName: '',
    businessType: '',
    industry: '',
    businessSize: '',
    yearsFounded: '',
    website: '',
    description: ''
  });
  
  const [businessGoals, setBusinessGoals] = useState({
    primaryGoals: [],
    revenueTarget: '',
    customerTarget: '',
    timeframe: '',
    challenges: []
  });
  
  const [selectedTools, setSelectedTools] = useState({
    tailorPacks: [],
    integrations: [],
    features: []
  });
  
  const [configuration, setConfiguration] = useState({
    dashboardLayout: 'comprehensive',
    notificationPreferences: [],
    dataSharing: false,
    autoBackup: true
  });

  const [wizardState, setWizardState] = useState({
    skipCalendar: false
  });

  const [calendarConnection, setCalendarConnection] = useState({
    provider: '',
    isConnected: false,
    email: ''
  });

  const businessTypes = [
    'Sole Proprietorship',
    'Partnership',
    'LLC',
    'Corporation',
    'Non-Profit',
    'Freelancer/Consultant',
    'Startup',
    'Other'
  ];

  const industries = [
    'Technology',
    'Healthcare',
    'Finance',
    'Retail/E-commerce',
    'Manufacturing',
    'Professional Services',
    'Real Estate',
    'Food & Beverage',
    'Education',
    'Marketing/Advertising',
    'Construction',
    'Transportation',
    'Other'
  ];

  const businessSizes = [
    'Solo (Just me)',
    'Small (2-10 employees)',
    'Medium (11-50 employees)',
    'Large (50+ employees)'
  ];

  const goalOptions = [
    'Increase Revenue',
    'Acquire New Customers',
    'Improve Operational Efficiency',
    'Expand Market Reach',
    'Enhance Customer Service',
    'Reduce Costs',
    'Launch New Products/Services',
    'Improve Team Productivity',
    'Better Financial Management',
    'Strengthen Brand Presence'
  ];

  const challengeOptions = [
    'Limited Time for Admin Tasks',
    'Difficulty Tracking Finances',
    'Customer Relationship Management',
    'Marketing and Lead Generation',
    'Inventory Management',
    'Employee Management',
    'Compliance and Legal Issues',
    'Technology Integration',
    'Data Organization',
    'Competition Analysis'
  ];

  const recommendedPacks = [
    {
      id: 'marketing-essentials',
      name: 'Marketing Essentials',
      description: 'Campaign tracking, social media management, lead generation',
      category: 'Marketing',
      recommended: true,
      reason: 'Perfect for building brand presence and acquiring customers'
    },
    {
      id: 'sales-pipeline-pro',
      name: 'Sales Pipeline Pro',
      description: 'Advanced CRM, deal tracking, sales analytics',
      category: 'Sales',
      recommended: true,
      reason: 'Essential for managing customer relationships and sales process'
    },
    {
      id: 'finance-master',
      name: 'Finance Master',
      description: 'Advanced accounting, tax preparation, financial planning',
      category: 'Finance',
      recommended: false,
      reason: 'Recommended for businesses with complex financial needs'
    },
    {
      id: 'legal-essentials',
      name: 'Legal Essentials',
      description: 'Contract templates, compliance tracking, legal advice',
      category: 'Legal',
      recommended: false,
      reason: 'Helpful for ensuring compliance and managing contracts'
    }
  ];

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleComplete = () => {
    const setupData = {
      businessProfile,
      businessGoals,
      calendarConnection,
      selectedTools,
      configuration,
      wizardState,
      setupCompletedAt: new Date().toISOString()
    };
    
    // Save setup data (in real app, this would be an API call)
    localStorage.setItem('businessSetup', JSON.stringify(setupData));
    
    onComplete?.(setupData);
  };

  const updateBusinessProfile = (field, value) => {
    setBusinessProfile(prev => ({ ...prev, [field]: value }));
  };

  const updateBusinessGoals = (field, value) => {
    setBusinessGoals(prev => ({ ...prev, [field]: value }));
  };

  const toggleArrayValue = (array, value, setter) => {
    const currentArray = Array.isArray(array) ? array : [];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    setter(newArray);
  };

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Tell us about your business
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              This information helps us customize the assistant for your specific needs.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Business Name"
                  value={businessProfile.businessName}
                  onChange={(e) => updateBusinessProfile('businessName', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Business Type</InputLabel>
                  <Select
                    value={businessProfile.businessType}
                    onChange={(e) => updateBusinessProfile('businessType', e.target.value)}
                  >
                    {businessTypes.map(type => (
                      <MenuItem key={type} value={type}>{type}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Industry</InputLabel>
                  <Select
                    value={businessProfile.industry}
                    onChange={(e) => updateBusinessProfile('industry', e.target.value)}
                  >
                    {industries.map(industry => (
                      <MenuItem key={industry} value={industry}>{industry}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth required>
                  <InputLabel>Business Size</InputLabel>
                  <Select
                    value={businessProfile.businessSize}
                    onChange={(e) => updateBusinessProfile('businessSize', e.target.value)}
                  >
                    {businessSizes.map(size => (
                      <MenuItem key={size} value={size}>{size}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Years in Business"
                  type="number"
                  value={businessProfile.yearsFounded}
                  onChange={(e) => updateBusinessProfile('yearsFounded', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Website (optional)"
                  value={businessProfile.website}
                  onChange={(e) => updateBusinessProfile('website', e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Business Description (optional)"
                  value={businessProfile.description}
                  onChange={(e) => updateBusinessProfile('description', e.target.value)}
                  placeholder="Briefly describe what your business does..."
                />
              </Grid>
            </Grid>
          </Box>
        );

      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              What are your business goals?
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Help us understand your priorities so we can recommend the best tools and features.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Primary Goals (select all that apply)
                </Typography>
                <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                  {goalOptions.map(goal => (
                    <Box key={goal} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Checkbox
                        checked={businessGoals.primaryGoals?.includes(goal) || false}
                        onChange={() => toggleArrayValue(
                          businessGoals.primaryGoals,
                          goal,
                          (newGoals) => updateBusinessGoals('primaryGoals', newGoals)
                        )}
                      />
                      <Typography variant="body2">{goal}</Typography>
                    </Box>
                  ))}
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Revenue Target (optional)"
                  placeholder="e.g., $100,000 this year"
                  value={businessGoals.revenueTarget}
                  onChange={(e) => updateBusinessGoals('revenueTarget', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Customer Target (optional)"
                  placeholder="e.g., 500 new customers"
                  value={businessGoals.customerTarget}
                  onChange={(e) => updateBusinessGoals('customerTarget', e.target.value)}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Current Challenges (select all that apply)
                </Typography>
                <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                  {challengeOptions.map(challenge => (
                    <Box key={challenge} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <Checkbox
                        checked={businessGoals.challenges?.includes(challenge) || false}
                        onChange={() => toggleArrayValue(
                          businessGoals.challenges,
                          challenge,
                          (newChallenges) => updateBusinessGoals('challenges', newChallenges)
                        )}
                      />
                      <Typography variant="body2">{challenge}</Typography>
                    </Box>
                  ))}
                </Paper>
              </Grid>
            </Grid>
          </Box>
        );

      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Connect Calendar
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Connect your calendar to sync appointments and improve scheduling efficiency.
            </Typography>
            
            {!calendarConnection.isConnected ? (
              <Box>
                <Alert severity="info" sx={{ mb: 3 }}>
                  Connecting your calendar helps the assistant track your availability and automatically schedule meetings.
                </Alert>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Calendar Provider</InputLabel>
                      <Select
                        value={calendarConnection.provider}
                        onChange={(e) => setCalendarConnection(prev => ({ ...prev, provider: e.target.value }))}
                      >
                        <MenuItem value="google">Google Calendar</MenuItem>
                        <MenuItem value="outlook">Microsoft Outlook</MenuItem>
                        <MenuItem value="apple">Apple iCloud</MenuItem>
                        <MenuItem value="exchange">Exchange Server</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  {calendarConnection.provider && (
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Email Address"
                        type="email"
                        value={calendarConnection.email}
                        onChange={(e) => setCalendarConnection(prev => ({ ...prev, email: e.target.value }))}
                        placeholder="Enter your calendar email address"
                      />
                    </Grid>
                  )}
                  
                  {calendarConnection.provider && calendarConnection.email && (
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        onClick={() => {
                          // Simulate calendar connection
                          setCalendarConnection(prev => ({ ...prev, isConnected: true }));
                        }}
                        sx={{ mr: 2 }}
                      >
                        Connect {calendarConnection.provider === 'google' ? 'Google Calendar' : 
                                calendarConnection.provider === 'outlook' ? 'Outlook' :
                                calendarConnection.provider === 'apple' ? 'Apple iCloud' :
                                calendarConnection.provider === 'exchange' ? 'Exchange Server' : 'Calendar'}
                      </Button>
                      
                      <Button
                        variant="outlined"
                        onClick={() => {
                          setWizardState(prev => ({ ...prev, skipCalendar: true }));
                        }}
                      >
                        Skip for Now
                      </Button>
                    </Grid>
                  )}
                  
                  {!calendarConnection.provider && (
                    <Grid item xs={12}>
                      <Button
                        variant="outlined"
                        onClick={() => {
                          setWizardState(prev => ({ ...prev, skipCalendar: true }));
                        }}
                      >
                        Skip for Now
                      </Button>
                    </Grid>
                  )}
                </Grid>
              </Box>
            ) : (
              <Box>
                <Alert severity="success" sx={{ mb: 3 }}>
                  Successfully connected to {calendarConnection.provider === 'google' ? 'Google Calendar' : 
                                             calendarConnection.provider === 'outlook' ? 'Outlook' :
                                             calendarConnection.provider === 'apple' ? 'Apple iCloud' :
                                             calendarConnection.provider === 'exchange' ? 'Exchange Server' : 'your calendar'}!
                </Alert>
                
                <Typography variant="body2" color="text.secondary">
                  Email: {calendarConnection.email}
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setCalendarConnection(prev => ({ ...prev, isConnected: false }))}
                  >
                    Disconnect
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
        );

      case 3:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recommended Tailor Packs
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Based on your business profile and goals, we recommend these specialized tool packs.
            </Typography>
            
            <Alert severity="info" sx={{ mb: 3 }}>
              All packs include a 30-day free trial. You can start with trials and upgrade later.
            </Alert>
            
            <Grid container spacing={2}>
              {recommendedPacks.map(pack => (
                <Grid item xs={12} md={6} key={pack.id}>
                  <Card 
                    elevation={pack.recommended ? 3 : 1}
                    sx={{ 
                      border: pack.recommended ? 2 : 1,
                      borderColor: pack.recommended ? 'primary.main' : 'divider',
                      position: 'relative'
                    }}
                  >
                    {pack.recommended && (
                      <Chip
                        label="Recommended"
                        color="primary"
                        size="small"
                        sx={{ position: 'absolute', top: 8, right: 8 }}
                      />
                    )}
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Checkbox
                          checked={selectedTools.tailorPacks?.includes(pack.id) || false}
                          onChange={() => toggleArrayValue(
                            selectedTools.tailorPacks,
                            pack.id,
                            (newPacks) => setSelectedTools(prev => ({ ...prev, tailorPacks: newPacks }))
                          )}
                        />
                        <Typography variant="h6">{pack.name}</Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {pack.description}
                      </Typography>
                      <Typography variant="caption" sx={{ fontStyle: 'italic' }}>
                        {pack.reason}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip label={pack.category} size="small" variant="outlined" />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        );

      case 4:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Configuration Preferences
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Customize how the assistant works for you.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Dashboard Layout</InputLabel>
                  <Select
                    value={configuration.dashboardLayout}
                    onChange={(e) => setConfiguration(prev => ({ ...prev, dashboardLayout: e.target.value }))}
                  >
                    <MenuItem value="simple">Simple - Key metrics only</MenuItem>
                    <MenuItem value="comprehensive">Comprehensive - All business data</MenuItem>
                    <MenuItem value="custom">Custom - I'll configure later</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Notification Preferences
                </Typography>
                <List>
                  {[
                    'New customer notifications',
                    'Revenue milestone alerts',
                    'Task due date reminders',
                    'Weekly business reports',
                    'Tailor Pack updates'
                  ].map(notification => (
                    <ListItem key={notification} sx={{ py: 0 }}>
                      <ListItemIcon>
                        <Checkbox
                          checked={configuration.notificationPreferences?.includes(notification) || false}
                          onChange={() => toggleArrayValue(
                            configuration.notificationPreferences,
                            notification,
                            (newNotifications) => setConfiguration(prev => ({ ...prev, notificationPreferences: newNotifications }))
                          )}
                        />
                      </ListItemIcon>
                      <ListItemText primary={notification} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              
              <Grid item xs={12}>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <Checkbox
                        checked={configuration.autoBackup}
                        onChange={(e) => setConfiguration(prev => ({ ...prev, autoBackup: e.target.checked }))}
                      />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Enable automatic backups"
                      secondary="Automatically backup your business data weekly"
                    />
                  </ListItem>
                </List>
              </Grid>
            </Grid>
          </Box>
        );

      case 5:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CheckCircleIcon color="success" />
              Setup Complete!
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Your Westfall Assistant is now configured for your business needs.
            </Typography>
            
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  Setup Summary
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Business Name</Typography>
                    <Typography variant="body1">{businessProfile.businessName || 'Not specified'}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Industry</Typography>
                    <Typography variant="body1">{businessProfile.industry || 'Not specified'}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">Selected Tailor Packs</Typography>
                    <Box sx={{ mt: 1 }}>
                      {selectedTools.tailorPacks?.length > 0 ? (
                        selectedTools.tailorPacks.map(packId => {
                          const pack = recommendedPacks.find(p => p.id === packId);
                          return pack ? (
                            <Chip key={packId} label={pack.name} sx={{ mr: 1, mb: 1 }} />
                          ) : null;
                        })
                      ) : (
                        <Typography variant="body2" color="text.secondary">None selected - you can add packs later</Typography>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
            
            <Alert severity="success">
              You're all set! You can now start using your business assistant. Remember that all Tailor Packs include a 30-day free trial.
            </Alert>
          </Box>
        );

      default:
        return 'Unknown step';
    }
  };

  const isStepValid = (step) => {
    switch (step) {
      case 0:
        return businessProfile.businessName && businessProfile.businessType && businessProfile.industry;
      case 1:
        return businessGoals.primaryGoals?.length > 0;
      case 2:
      case 3:
      case 4:
        return true; // These steps are optional
      default:
        return true;
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ textAlign: 'center' }}>
        Welcome to Westfall Assistant
      </Typography>
      <Typography variant="subtitle1" sx={{ textAlign: 'center', mb: 4, color: 'text.secondary' }}>
        Let's set up your business assistant in just a few steps
      </Typography>

      <Stepper activeStep={activeStep} orientation="vertical">
        {steps.map((label, index) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
            <StepContent>
              {getStepContent(index)}
              <Box sx={{ mb: 2, mt: 3 }}>
                <Button
                  variant="contained"
                  onClick={index === steps.length - 1 ? handleComplete : handleNext}
                  disabled={!isStepValid(index)}
                  sx={{ mr: 1 }}
                >
                  {index === steps.length - 1 ? 'Complete Setup' : 'Continue'}
                </Button>
                <Button
                  disabled={index === 0}
                  onClick={handleBack}
                  sx={{ mr: 1 }}
                >
                  Back
                </Button>
                {index === 0 && (
                  <Button onClick={onSkip} color="secondary">
                    Skip Setup
                  </Button>
                )}
              </Box>
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
}