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

  // Mock business data - replace with real API calls
  const businessMetrics = {
    revenue: {
      current: '$12,450',
      change: '+15.2% vs last month',
      changeType: 'positive'
    },
    customers: {
      current: '847',
      change: '+23 new this month',
      changeType: 'positive'
    },
    orders: {
      current: '156',
      change: '-5.1% vs last month',
      changeType: 'negative'
    },
    avgDeal: {
      current: '$1,234',
      change: '+8.7% vs last month',
      changeType: 'positive'
    }
  };

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
      type: 'email', 
      icon: EmailIcon, 
      text: 'Proposal sent to TechStart Inc', 
      time: '6 hours ago',
      color: 'primary'
    },
    { 
      type: 'meeting', 
      icon: EventIcon, 
      text: 'Completed call with Product Manager at Beta Co', 
      time: '1 day ago',
      color: 'secondary'
    }
  ];

  const monthlyGoals = [
    { title: 'Monthly Revenue', current: 12450, target: 20000, unit: '$' },
    { title: 'New Customers', current: 23, target: 30, unit: '' },
    { title: 'Closed Deals', current: 8, target: 12, unit: '' },
    { title: 'Meeting Hours', current: 42, target: 60, unit: 'h' }
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

      <Grid container spacing={3}>
        {/* Monthly Goals */}
        <Grid item xs={12} md={6}>
          <Card elevation={2}>
            <CardContent>
              <Typography variant="h6" component="h3" gutterBottom>
                📈 Monthly Goals
              </Typography>
              {monthlyGoals.map((goal, index) => (
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
    </Box>
  );
}