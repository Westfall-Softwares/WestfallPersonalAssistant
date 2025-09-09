import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Button,
  LinearProgress,
  IconButton,
  Menu,
  MenuItem
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as AttachMoneyIcon,
  People as PeopleIcon,
  ShoppingCart as ShoppingCartIcon,
  AccessTime as AccessTimeIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Event as EventIcon,
  Task as TaskIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

const MetricCard = ({ title, value, change, changeType, icon, color = 'primary' }) => {
  const IconComponent = icon;
  
  return (
    <Card elevation={2}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h6" component="h3" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold', mb: 1 }}>
              {value}
            </Typography>
            {change && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {changeType === 'positive' ? (
                  <TrendingUpIcon sx={{ color: 'success.main', fontSize: 16 }} />
                ) : (
                  <TrendingDownIcon sx={{ color: 'error.main', fontSize: 16 }} />
                )}
                <Typography 
                  variant="body2" 
                  color={changeType === 'positive' ? 'success.main' : 'error.main'}
                >
                  {change}
                </Typography>
              </Box>
            )}
          </Box>
          <Box sx={{ 
            backgroundColor: `${color}.light`, 
            borderRadius: 2, 
            p: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <IconComponent sx={{ color: `${color}.main`, fontSize: 32 }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const GoalProgress = ({ title, current, target, unit = '' }) => {
  const percentage = Math.min((current / target) * 100, 100);
  
  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
        <Typography variant="body2" fontWeight="medium">{title}</Typography>
        <Typography variant="body2" color="text.secondary">
          {current}{unit} / {target}{unit}
        </Typography>
      </Box>
      <LinearProgress 
        variant="determinate" 
        value={percentage}
        sx={{ height: 8, borderRadius: 4 }}
      />
      <Typography variant="caption" color="text.secondary">
        {percentage.toFixed(1)}% complete
      </Typography>
    </Box>
  );
};

export default function BusinessDashboard() {
  const [refreshTime, setRefreshTime] = useState(new Date());
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('month');

  // Enhanced business data with more comprehensive metrics
  const businessMetrics = {
    revenue: {
      current: '$12,450',
      change: '+15.2% vs last month',
      changeType: 'positive',
      target: '$15,000',
      progress: 83
    },
    customers: {
      current: '847',
      change: '+23 new this month',
      changeType: 'positive',
      target: '1,000',
      progress: 85
    },
    orders: {
      current: '156',
      change: '-5.1% vs last month',
      changeType: 'negative',
      target: '175',
      progress: 89
    },
    avgDeal: {
      current: '$1,234',
      change: '+8.7% vs last month',
      changeType: 'positive',
      target: '$1,500',
      progress: 82
    },
    // New entrepreneur-focused metrics
    burnRate: {
      current: '$3,200',
      change: '-12% vs last month',
      changeType: 'positive',
      description: 'Monthly burn rate'
    },
    cashflow: {
      current: '$8,750',
      change: '+24% vs last month',
      changeType: 'positive',
      description: 'Net cash flow'
    },
    runway: {
      current: '18 months',
      change: '+2 months vs last calc',
      changeType: 'positive',
      description: 'Cash runway'
    },
    conversionRate: {
      current: '3.2%',
      change: '+0.8% vs last month',
      changeType: 'positive',
      description: 'Lead conversion rate'
    }
  };

  const entrepreneurKPIs = [
    { name: 'Customer Acquisition Cost', value: '$125', target: '$100', status: 'warning' },
    { name: 'Lifetime Value', value: '$2,450', target: '$2,000', status: 'success' },
    { name: 'Monthly Recurring Revenue', value: '$8,200', target: '$10,000', status: 'info' },
    { name: 'Churn Rate', value: '2.1%', target: '<3%', status: 'success' },
    { name: 'Product Market Fit Score', value: '7.8/10', target: '8.0', status: 'warning' },
    { name: 'Net Promoter Score', value: '67', target: '70', status: 'info' }
  ];

  const businessGoals = [
    { title: 'Q4 Revenue Target', current: 42500, target: 60000, unit: '$' },
    { title: 'Customer Growth', current: 847, target: 1000, unit: '' },
    { title: 'Product Development', current: 7, target: 10, unit: ' features' },
    { title: 'Market Expansion', current: 3, target: 5, unit: ' cities' },
    { title: 'Team Growth', current: 12, target: 15, unit: ' employees' },
    { title: 'Funding Round', current: 250000, target: 500000, unit: '$' }
  ];

  const recentActivity = [
    { 
      type: 'sale', 
      icon: ShoppingCartIcon, 
      text: 'New order from Acme Corp - $2,500', 
      time: '2 hours ago',
      color: 'success'
    },
    { 
      type: 'customer', 
      icon: PeopleIcon, 
      text: 'John Smith updated contact information', 
      time: '4 hours ago',
      color: 'info'
    },
    { 
      type: 'funding', 
      icon: AttachMoneyIcon, 
      text: 'Investment inquiry from VC firm', 
      time: '6 hours ago',
      color: 'warning'
    },
    { 
      type: 'product', 
      icon: TaskIcon, 
      text: 'New feature deployed to production', 
      time: '8 hours ago',
      color: 'info'
    },
    { 
      type: 'team', 
      icon: PeopleIcon, 
      text: 'New developer started today', 
      time: '1 day ago',
      color: 'success'
    }
  ];

  const upcomingTasks = [
    { task: 'Follow up with ProTech Industries', priority: 'high', due: 'Today' },
    { task: 'Prepare Q4 financial report', priority: 'medium', due: 'Tomorrow' },
    { task: 'Review marketing campaign performance', priority: 'low', due: 'This week' },
    { task: 'Schedule team planning meeting', priority: 'medium', due: 'Next week' }
  ];

  const handleRefresh = () => {
    setRefreshTime(new Date());
    // Trigger data refresh here
    console.log('Refreshing dashboard data...');
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            📊 Business Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Last updated: {refreshTime.toLocaleTimeString()}
          </Typography>
        </Box>
        <Box>
          <IconButton onClick={handleRefresh} sx={{ mr: 1 }}>
            <RefreshIcon />
          </IconButton>
          <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
            <MoreVertIcon />
          </IconButton>
          <Menu
            anchorEl={menuAnchor}
            open={Boolean(menuAnchor)}
            onClose={() => setMenuAnchor(null)}
          >
            <MenuItem onClick={() => setMenuAnchor(null)}>Export Data</MenuItem>
            <MenuItem onClick={() => setMenuAnchor(null)}>Configure Widgets</MenuItem>
            <MenuItem onClick={() => setMenuAnchor(null)}>Dashboard Settings</MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Monthly Revenue"
            value={businessMetrics.revenue.current}
            change={businessMetrics.revenue.change}
            changeType={businessMetrics.revenue.changeType}
            icon={AttachMoneyIcon}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Total Customers"
            value={businessMetrics.customers.current}
            change={businessMetrics.customers.change}
            changeType={businessMetrics.customers.changeType}
            icon={PeopleIcon}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Monthly Orders"
            value={businessMetrics.orders.current}
            change={businessMetrics.orders.change}
            changeType={businessMetrics.orders.changeType}
            icon={ShoppingCartIcon}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Deal Size"
            value={businessMetrics.avgDeal.current}
            change={businessMetrics.avgDeal.change}
            changeType={businessMetrics.avgDeal.changeType}
            icon={TrendingUpIcon}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Entrepreneur Enhancement Recommendations */}
      <Card elevation={2} sx={{ mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" component="h3" sx={{ color: 'white', fontWeight: 'bold' }}>
              🚀 Growth Opportunities
            </Typography>
            <Chip 
              label="AI-Powered" 
              size="small" 
              sx={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
            />
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  📦 Recommended Tailor Packs
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                  • <strong>Sales Pipeline Pro</strong> - Boost conversions by 25%
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                  • <strong>Marketing Automation</strong> - Save 10+ hours/week
                </Typography>
                <Button 
                  variant="outlined" 
                  size="small" 
                  sx={{ 
                    color: 'white', 
                    borderColor: 'white',
                    '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
                  }}
                >
                  Explore Packs
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  📈 Performance Insights
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                  • Customer acquisition cost decreased 12%
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                  • Revenue per customer increased $156
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  • Peak sales hours: 2-4 PM
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  🎯 Next Action Items
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                  • Schedule follow-up with 3 warm leads
                </Typography>
                <Typography variant="body2" sx={{ mb: 1, opacity: 0.9 }}>
                  • Review and optimize top-performing campaigns
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  • Update pricing strategy based on market analysis
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Monthly Goals */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                📈 Monthly Goals
              </Typography>
              {businessGoals.slice(0, 4).map((goal, index) => (
                <GoalProgress
                  key={index}
                  title={goal.title}
                  current={goal.current}
                  target={goal.target}
                  unit={goal.unit}
                />
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                🕒 Recent Activity
              </Typography>
              <List>
                {recentActivity.map((activity, index) => {
                  const IconComponent = activity.icon;
                  return (
                    <ListItem key={index} sx={{ px: 0 }}>
                      <ListItemIcon>
                        <IconComponent color={activity.color} />
                      </ListItemIcon>
                      <ListItemText
                        primary={activity.text}
                        secondary={activity.time}
                      />
                    </ListItem>
                  );
                })}
              </List>
              <Button variant="outlined" fullWidth sx={{ mt: 2 }}>
                View All Activity
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Upcoming Tasks */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                ✅ Upcoming Tasks
              </Typography>
              <List>
                {upcomingTasks.map((task, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon>
                      <TaskIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={task.task}
                      secondary={task.due}
                    />
                    <Chip
                      label={task.priority}
                      size="small"
                      color={getPriorityColor(task.priority)}
                    />
                  </ListItem>
                ))}
              </List>
              <Button variant="outlined" fullWidth sx={{ mt: 2 }}>
                Manage Tasks
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                🚀 Quick Actions
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    startIcon={<PeopleIcon />}
                    sx={{ mb: 1 }}
                  >
                    Add Customer
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    startIcon={<ShoppingCartIcon />}
                    sx={{ mb: 1 }}
                  >
                    New Order
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    startIcon={<EmailIcon />}
                    sx={{ mb: 1 }}
                  >
                    Send Proposal
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button 
                    variant="outlined" 
                    fullWidth 
                    startIcon={<EventIcon />}
                    sx={{ mb: 1 }}
                  >
                    Schedule Meeting
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Entrepreneur KPIs Section */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                💼 Entrepreneur KPIs
              </Typography>
              <Grid container spacing={2}>
                {entrepreneurKPIs.map((kpi, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Paper 
                      elevation={1} 
                      sx={{ 
                        p: 2, 
                        textAlign: 'center',
                        borderLeft: `4px solid ${
                          kpi.status === 'success' ? '#4caf50' :
                          kpi.status === 'warning' ? '#ff9800' :
                          kpi.status === 'error' ? '#f44336' : '#2196f3'
                        }`
                      }}
                    >
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {kpi.name}
                      </Typography>
                      <Typography variant="h6" fontWeight="bold">
                        {kpi.value}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Target: {kpi.target}
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Enhanced Business Financial Metrics */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Monthly Burn Rate"
            value={businessMetrics.burnRate.current}
            change={businessMetrics.burnRate.change}
            changeType={businessMetrics.burnRate.changeType}
            icon={TrendingDownIcon}
            color="warning"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Net Cash Flow"
            value={businessMetrics.cashflow.current}
            change={businessMetrics.cashflow.change}
            changeType={businessMetrics.cashflow.changeType}
            icon={AttachMoneyIcon}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Cash Runway"
            value={businessMetrics.runway.current}
            change={businessMetrics.runway.change}
            changeType={businessMetrics.runway.changeType}
            icon={AccessTimeIcon}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Conversion Rate"
            value={businessMetrics.conversionRate.current}
            change={businessMetrics.conversionRate.change}
            changeType={businessMetrics.conversionRate.changeType}
            icon={TrendingUpIcon}
            color="primary"
          />
        </Grid>
      </Grid>

      {/* Business Goals Section */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                🎯 Strategic Business Goals
              </Typography>
              <Grid container spacing={2}>
                {businessGoals.map((goal, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <GoalProgress
                      title={goal.title}
                      current={goal.current}
                      target={goal.target}
                      unit={goal.unit}
                    />
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

    </Box>
  );
}