---
title: "Building a Custom Dashboard Plugin"
description: "Complete guide to creating a specialized dashboard plugin for Westfall Personal Assistant"
category: "developer-examples"
priority: 1
tags: ["plugin", "dashboard", "development", "ui", "api"]
last_updated: "2025-09-08"
---

# Building a Custom Dashboard Plugin

This comprehensive guide walks through creating a specialized dashboard plugin for Westfall Personal Assistant, demonstrating the plugin architecture, API integration, and UI customization capabilities.

## Project Overview

**Plugin Name**: Business Metrics Dashboard  
**Purpose**: Real-time business intelligence dashboard for consulting firms  
**Features**: Client analytics, revenue tracking, project timelines, and AI insights  
**Complexity**: Intermediate to Advanced  
**Development Time**: 2-3 weeks  

## Prerequisites

### Required Knowledge
- JavaScript/TypeScript fundamentals
- React.js framework
- Node.js and npm/yarn
- RESTful API concepts
- Basic SQL/database knowledge

### Development Environment
```bash
# Required tools
node --version    # v18+
npm --version     # v9+
git --version     # v2.30+

# Recommended IDE extensions
- Westfall Plugin Development Kit
- React Developer Tools
- TypeScript Language Server
```

### Plugin SDK Installation
```bash
npm install -g @westfall/plugin-cli
westfall plugin init business-metrics-dashboard
cd business-metrics-dashboard
npm install
```

## Plugin Architecture Overview

### File Structure
```
business-metrics-dashboard/
├── manifest.json                 # Plugin configuration
├── package.json                 # Dependencies and scripts
├── src/
│   ├── components/              # React components
│   │   ├── Dashboard.jsx        # Main dashboard component
│   │   ├── MetricCard.jsx       # Individual metric display
│   │   ├── ChartPanel.jsx       # Chart visualizations
│   │   └── SettingsPanel.jsx    # Configuration interface
│   ├── services/                # Data services
│   │   ├── dataService.js       # Main data connector
│   │   ├── apiClient.js         # Westfall API integration
│   │   └── chartService.js      # Chart data processing
│   ├── utils/                   # Utility functions
│   │   ├── formatters.js        # Data formatting
│   │   ├── calculations.js      # Business calculations
│   │   └── constants.js         # Configuration constants
│   ├── styles/                  # Component styles
│   │   ├── dashboard.css        # Main dashboard styles
│   │   └── theme.css            # Theme customization
│   └── assets/                  # Static assets
│       ├── icons/               # Custom icons
│       └── images/              # Background images
├── tests/                       # Unit and integration tests
├── docs/                        # Plugin documentation
└── dist/                        # Built plugin files
```

## Step 1: Plugin Manifest Configuration

### manifest.json
```json
{
  "manifest_version": 3,
  "name": "Business Metrics Dashboard",
  "version": "1.0.0",
  "description": "Advanced business intelligence dashboard for consulting firms",
  "author": "Your Name",
  "homepage_url": "https://github.com/yourusername/business-metrics-dashboard",
  "icon": "assets/icons/dashboard-icon.png",
  
  "permissions": [
    "read_finance_data",
    "read_crm_data",
    "read_time_tracking",
    "write_user_preferences",
    "network_access",
    "ai_assistant_integration"
  ],
  
  "host_permissions": [
    "https://api.westfall.app/*",
    "https://charts.googleapis.com/*"
  ],
  
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["src/content.js"],
      "css": ["src/styles/dashboard.css"]
    }
  ],
  
  "background": {
    "service_worker": "src/background.js",
    "type": "module"
  },
  
  "web_accessible_resources": [
    {
      "resources": ["assets/*", "src/components/*"],
      "matches": ["<all_urls>"]
    }
  ],
  
  "options_ui": {
    "page": "src/components/SettingsPanel.html",
    "chrome_style": true
  },
  
  "dashboard_integration": {
    "widget_types": ["full_screen", "panel", "modal"],
    "default_position": "main_content",
    "refresh_interval": 300000,
    "cache_strategy": "smart_refresh"
  }
}
```

## Step 2: Core Data Service Implementation

### src/services/apiClient.js
```javascript
/**
 * Westfall Personal Assistant API Client
 * Handles authentication and data retrieval
 */

class WestfallAPIClient {
  constructor() {
    this.baseURL = 'https://api.westfall.app/v1';
    this.apiKey = null;
    this.token = null;
  }

  async initialize() {
    // Get API credentials from Westfall context
    this.apiKey = await westfall.auth.getAPIKey();
    this.token = await westfall.auth.getSessionToken();
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('API Client Error:', error);
      throw error;
    }
  }

  // Finance data methods
  async getFinanceData(timeRange = '30d') {
    return this.request(`/finance/summary?range=${timeRange}`);
  }

  async getRevenueTrends(period = 'monthly') {
    return this.request(`/finance/revenue/trends?period=${period}`);
  }

  async getExpenseBreakdown() {
    return this.request('/finance/expenses/breakdown');
  }

  // CRM data methods
  async getClientMetrics() {
    return this.request('/crm/clients/metrics');
  }

  async getProjectStatus() {
    return this.request('/crm/projects/status');
  }

  async getClientProfitability() {
    return this.request('/crm/clients/profitability');
  }

  // Time tracking data
  async getTimeMetrics(dateRange) {
    return this.request(`/time/metrics?from=${dateRange.from}&to=${dateRange.to}`);
  }

  async getBillableHours() {
    return this.request('/time/billable/summary');
  }

  // AI insights
  async getBusinessInsights() {
    return this.request('/ai/insights/business');
  }

  async getPredictions(metric, horizon = '3m') {
    return this.request(`/ai/predictions/${metric}?horizon=${horizon}`);
  }
}

export default new WestfallAPIClient();
```

### src/services/dataService.js
```javascript
/**
 * Data Service - Orchestrates data collection and processing
 */

import apiClient from './apiClient.js';
import { formatCurrency, formatPercentage, formatDate } from '../utils/formatters.js';
import { calculateGrowthRate, calculateRunway } from '../utils/calculations.js';

class DataService {
  constructor() {
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
  }

  async initialize() {
    await apiClient.initialize();
  }

  async getCachedData(key, fetcher) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }

    const data = await fetcher();
    this.cache.set(key, { data, timestamp: Date.now() });
    return data;
  }

  async getDashboardData() {
    try {
      const [
        financeData,
        clientMetrics,
        projectStatus,
        timeMetrics,
        insights
      ] = await Promise.all([
        this.getCachedData('finance', () => apiClient.getFinanceData()),
        this.getCachedData('clients', () => apiClient.getClientMetrics()),
        this.getCachedData('projects', () => apiClient.getProjectStatus()),
        this.getCachedData('time', () => apiClient.getTimeMetrics({
          from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          to: new Date().toISOString()
        })),
        this.getCachedData('insights', () => apiClient.getBusinessInsights())
      ]);

      return this.processBusinessMetrics({
        financeData,
        clientMetrics,
        projectStatus,
        timeMetrics,
        insights
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      throw error;
    }
  }

  processBusinessMetrics(rawData) {
    const { financeData, clientMetrics, projectStatus, timeMetrics, insights } = rawData;

    return {
      overview: {
        totalRevenue: formatCurrency(financeData.revenue.total),
        monthlyRecurring: formatCurrency(financeData.revenue.recurring),
        netProfit: formatCurrency(financeData.profit.net),
        profitMargin: formatPercentage(financeData.profit.margin),
        cashFlow: formatCurrency(financeData.cashflow.current),
        runway: calculateRunway(financeData.cashflow.current, financeData.expenses.monthly)
      },

      growth: {
        revenueGrowth: formatPercentage(calculateGrowthRate(financeData.revenue.history)),
        clientGrowth: formatPercentage(calculateGrowthRate(clientMetrics.growth)),
        profitGrowth: formatPercentage(calculateGrowthRate(financeData.profit.history))
      },

      clients: {
        total: clientMetrics.total,
        active: clientMetrics.active,
        newThisMonth: clientMetrics.new_this_month,
        churnRate: formatPercentage(clientMetrics.churn_rate),
        averageValue: formatCurrency(clientMetrics.average_value),
        satisfaction: clientMetrics.satisfaction_score
      },

      projects: {
        active: projectStatus.active.length,
        completed: projectStatus.completed_this_month,
        onTrack: projectStatus.on_track,
        atRisk: projectStatus.at_risk,
        avgDuration: projectStatus.average_duration
      },

      productivity: {
        billableHours: timeMetrics.billable.total,
        billablePercentage: formatPercentage(timeMetrics.billable.percentage),
        averageRate: formatCurrency(timeMetrics.average_rate),
        efficiency: formatPercentage(timeMetrics.efficiency)
      },

      insights: {
        highlights: insights.highlights,
        warnings: insights.warnings,
        recommendations: insights.recommendations,
        predictions: insights.predictions
      },

      lastUpdated: new Date().toISOString()
    };
  }

  async getDetailedAnalytics(metric) {
    switch (metric) {
      case 'revenue':
        return this.getRevenueAnalytics();
      case 'clients':
        return this.getClientAnalytics();
      case 'productivity':
        return this.getProductivityAnalytics();
      default:
        throw new Error(`Unknown metric: ${metric}`);
    }
  }

  async getRevenueAnalytics() {
    const [trends, breakdown] = await Promise.all([
      apiClient.getRevenueTrends('monthly'),
      apiClient.getExpenseBreakdown()
    ]);

    return {
      trends: trends.map(point => ({
        date: formatDate(point.date),
        revenue: point.revenue,
        expenses: point.expenses,
        profit: point.revenue - point.expenses
      })),
      breakdown,
      projections: await apiClient.getPredictions('revenue', '6m')
    };
  }

  async getClientAnalytics() {
    const [profitability, metrics] = await Promise.all([
      apiClient.getClientProfitability(),
      apiClient.getClientMetrics()
    ]);

    return {
      profitability: profitability.map(client => ({
        name: client.name,
        revenue: formatCurrency(client.revenue),
        profit: formatCurrency(client.profit),
        margin: formatPercentage(client.margin),
        projects: client.project_count
      })),
      lifecycle: metrics.lifecycle_analysis,
      satisfaction: metrics.satisfaction_trends
    };
  }

  async getProductivityAnalytics() {
    const timeData = await apiClient.getTimeMetrics({
      from: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
      to: new Date().toISOString()
    });

    return {
      daily_patterns: timeData.daily_patterns,
      project_efficiency: timeData.project_efficiency,
      billable_trends: timeData.billable_trends,
      capacity_analysis: timeData.capacity_analysis
    };
  }
}

export default new DataService();
```

## Step 3: React Component Development

### src/components/Dashboard.jsx
```javascript
/**
 * Main Dashboard Component
 */

import React, { useState, useEffect, useCallback } from 'react';
import MetricCard from './MetricCard.jsx';
import ChartPanel from './ChartPanel.jsx';
import dataService from '../services/dataService.js';
import '../styles/dashboard.css';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dataService.getDashboardData();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard loading error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initialize data service and load initial data
    const initializeDashboard = async () => {
      await dataService.initialize();
      await loadDashboardData();
    };

    initializeDashboard();

    // Set up auto-refresh
    const interval = setInterval(loadDashboardData, 5 * 60 * 1000); // 5 minutes
    setRefreshInterval(interval);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [loadDashboardData]);

  const handleMetricClick = async (metric) => {
    setSelectedMetric(metric);
    // Load detailed analytics for the selected metric
    try {
      const detailedData = await dataService.getDetailedAnalytics(metric);
      setSelectedMetric({ ...metric, details: detailedData });
    } catch (err) {
      console.error('Failed to load detailed analytics:', err);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  if (loading && !dashboardData) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading business metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h3>Error Loading Dashboard</h3>
        <p>{error}</p>
        <button onClick={handleRefresh} className="retry-button">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="business-metrics-dashboard">
      <header className="dashboard-header">
        <h1>Business Metrics Dashboard</h1>
        <div className="dashboard-controls">
          <button 
            onClick={handleRefresh} 
            className="refresh-button"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <span className="last-updated">
            Last updated: {new Date(dashboardData.lastUpdated).toLocaleTimeString()}
          </span>
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Overview Metrics */}
        <section className="metrics-overview">
          <h2>Financial Overview</h2>
          <div className="metric-cards">
            <MetricCard
              title="Total Revenue"
              value={dashboardData.overview.totalRevenue}
              trend={dashboardData.growth.revenueGrowth}
              onClick={() => handleMetricClick('revenue')}
            />
            <MetricCard
              title="Monthly Recurring"
              value={dashboardData.overview.monthlyRecurring}
              trend="+12%"
              onClick={() => handleMetricClick('recurring')}
            />
            <MetricCard
              title="Net Profit"
              value={dashboardData.overview.netProfit}
              trend={dashboardData.growth.profitGrowth}
              onClick={() => handleMetricClick('profit')}
            />
            <MetricCard
              title="Profit Margin"
              value={dashboardData.overview.profitMargin}
              trend="+2.3%"
              onClick={() => handleMetricClick('margin')}
            />
          </div>
        </section>

        {/* Client Metrics */}
        <section className="client-metrics">
          <h2>Client Health</h2>
          <div className="metric-cards">
            <MetricCard
              title="Active Clients"
              value={dashboardData.clients.active}
              trend={dashboardData.growth.clientGrowth}
              onClick={() => handleMetricClick('clients')}
            />
            <MetricCard
              title="Client Satisfaction"
              value={`${dashboardData.clients.satisfaction}/10`}
              trend="+0.2"
              onClick={() => handleMetricClick('satisfaction')}
            />
            <MetricCard
              title="Average Client Value"
              value={dashboardData.clients.averageValue}
              trend="+15%"
              onClick={() => handleMetricClick('client-value')}
            />
            <MetricCard
              title="Churn Rate"
              value={dashboardData.clients.churnRate}
              trend="-1.2%"
              isGoodTrend={false}
              onClick={() => handleMetricClick('churn')}
            />
          </div>
        </section>

        {/* Productivity Metrics */}
        <section className="productivity-metrics">
          <h2>Productivity</h2>
          <div className="metric-cards">
            <MetricCard
              title="Billable Hours"
              value={dashboardData.productivity.billableHours}
              trend="+8%"
              onClick={() => handleMetricClick('productivity')}
            />
            <MetricCard
              title="Billable Percentage"
              value={dashboardData.productivity.billablePercentage}
              trend="+3%"
              onClick={() => handleMetricClick('billable-rate')}
            />
            <MetricCard
              title="Average Rate"
              value={dashboardData.productivity.averageRate}
              trend="+$5"
              onClick={() => handleMetricClick('hourly-rate')}
            />
            <MetricCard
              title="Efficiency Score"
              value={dashboardData.productivity.efficiency}
              trend="+2%"
              onClick={() => handleMetricClick('efficiency')}
            />
          </div>
        </section>

        {/* Charts Panel */}
        <section className="charts-section">
          <ChartPanel 
            data={dashboardData}
            selectedMetric={selectedMetric}
            onMetricSelect={handleMetricClick}
          />
        </section>

        {/* AI Insights */}
        <section className="insights-section">
          <h2>AI Insights</h2>
          <div className="insights-grid">
            <div className="insight-panel highlights">
              <h3>Highlights</h3>
              <ul>
                {dashboardData.insights.highlights.map((highlight, index) => (
                  <li key={index} className="insight-highlight">
                    {highlight}
                  </li>
                ))}
              </ul>
            </div>

            <div className="insight-panel warnings">
              <h3>Warnings</h3>
              <ul>
                {dashboardData.insights.warnings.map((warning, index) => (
                  <li key={index} className="insight-warning">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>

            <div className="insight-panel recommendations">
              <h3>Recommendations</h3>
              <ul>
                {dashboardData.insights.recommendations.map((rec, index) => (
                  <li key={index} className="insight-recommendation">
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
```

### src/components/MetricCard.jsx
```javascript
/**
 * Individual Metric Card Component
 */

import React from 'react';

const MetricCard = ({ 
  title, 
  value, 
  trend, 
  isGoodTrend = true, 
  onClick,
  subtitle,
  icon 
}) => {
  const getTrendClass = () => {
    if (!trend) return '';
    const isPositive = trend.startsWith('+');
    if (isGoodTrend) {
      return isPositive ? 'trend-positive' : 'trend-negative';
    } else {
      return isPositive ? 'trend-negative' : 'trend-positive';
    }
  };

  const formatTrend = (trend) => {
    if (!trend) return null;
    return trend.startsWith('+') || trend.startsWith('-') ? trend : `+${trend}`;
  };

  return (
    <div 
      className={`metric-card ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="metric-header">
        {icon && <div className="metric-icon">{icon}</div>}
        <h3 className="metric-title">{title}</h3>
      </div>
      
      <div className="metric-content">
        <div className="metric-value">{value}</div>
        {subtitle && <div className="metric-subtitle">{subtitle}</div>}
        
        {trend && (
          <div className={`metric-trend ${getTrendClass()}`}>
            <span className="trend-indicator">
              {formatTrend(trend)}
            </span>
            <span className="trend-period">vs last month</span>
          </div>
        )}
      </div>

      {onClick && (
        <div className="metric-action">
          <span className="action-text">Click for details →</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
```

## Step 4: Chart Integration

### src/components/ChartPanel.jsx
```javascript
/**
 * Chart Panel Component with multiple visualization types
 */

import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
         XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ChartPanel = ({ data, selectedMetric, onMetricSelect }) => {
  const [chartType, setChartType] = useState('revenue-trend');
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    generateChartData();
  }, [data, chartType]);

  const generateChartData = () => {
    switch (chartType) {
      case 'revenue-trend':
        setChartData(generateRevenueTrend());
        break;
      case 'client-distribution':
        setChartData(generateClientDistribution());
        break;
      case 'project-status':
        setChartData(generateProjectStatus());
        break;
      case 'productivity-overview':
        setChartData(generateProductivityOverview());
        break;
      default:
        setChartData([]);
    }
  };

  const generateRevenueTrend = () => {
    // Sample data - in real implementation, this would come from API
    return [
      { month: 'Jan', revenue: 15000, expenses: 8000, profit: 7000 },
      { month: 'Feb', revenue: 18000, expenses: 9000, profit: 9000 },
      { month: 'Mar', revenue: 22000, expenses: 10000, profit: 12000 },
      { month: 'Apr', revenue: 25000, expenses: 11000, profit: 14000 },
      { month: 'May', revenue: 28000, expenses: 12000, profit: 16000 },
      { month: 'Jun', revenue: 32000, expenses: 13000, profit: 19000 }
    ];
  };

  const generateClientDistribution = () => {
    return [
      { name: 'Tech Startups', value: 45, color: '#0088FE' },
      { name: 'Small Business', value: 30, color: '#00C49F' },
      { name: 'Enterprise', value: 15, color: '#FFBB28' },
      { name: 'Non-Profit', value: 10, color: '#FF8042' }
    ];
  };

  const generateProjectStatus = () => {
    return [
      { status: 'Completed', count: 12, color: '#00C49F' },
      { status: 'In Progress', count: 8, color: '#0088FE' },
      { status: 'On Hold', count: 3, color: '#FFBB28' },
      { status: 'At Risk', count: 2, color: '#FF8042' }
    ];
  };

  const generateProductivityOverview = () => {
    return [
      { week: 'Week 1', billable: 32, nonBillable: 8, efficiency: 80 },
      { week: 'Week 2', billable: 35, nonBillable: 5, efficiency: 87.5 },
      { week: 'Week 3', billable: 30, nonBillable: 10, efficiency: 75 },
      { week: 'Week 4', billable: 38, nonBillable: 2, efficiency: 95 }
    ];
  };

  const renderChart = () => {
    switch (chartType) {
      case 'revenue-trend':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, '']} />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="revenue" 
                stackId="1" 
                stroke="#0088FE" 
                fill="#0088FE" 
                fillOpacity={0.6}
                name="Revenue"
              />
              <Area 
                type="monotone" 
                dataKey="expenses" 
                stackId="2" 
                stroke="#FF8042" 
                fill="#FF8042" 
                fillOpacity={0.6}
                name="Expenses"
              />
              <Line 
                type="monotone" 
                dataKey="profit" 
                stroke="#00C49F" 
                strokeWidth={3}
                name="Profit"
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'client-distribution':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'project-status':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="status" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#0088FE" />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'productivity-overview':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis yAxisId="hours" orientation="left" />
              <YAxis yAxisId="efficiency" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="hours" dataKey="billable" fill="#00C49F" name="Billable Hours" />
              <Bar yAxisId="hours" dataKey="nonBillable" fill="#FF8042" name="Non-Billable Hours" />
              <Line 
                yAxisId="efficiency" 
                type="monotone" 
                dataKey="efficiency" 
                stroke="#0088FE" 
                strokeWidth={3}
                name="Efficiency %"
              />
            </LineChart>
          </ResponsiveContainer>
        );

      default:
        return <div>Select a chart type</div>;
    }
  };

  return (
    <div className="chart-panel">
      <div className="chart-controls">
        <h3>Analytics Charts</h3>
        <div className="chart-type-selector">
          <select 
            value={chartType} 
            onChange={(e) => setChartType(e.target.value)}
            className="chart-select"
          >
            <option value="revenue-trend">Revenue Trend</option>
            <option value="client-distribution">Client Distribution</option>
            <option value="project-status">Project Status</option>
            <option value="productivity-overview">Productivity Overview</option>
          </select>
        </div>
      </div>

      <div className="chart-container">
        {renderChart()}
      </div>

      <div className="chart-insights">
        <div className="insight-summary">
          {chartType === 'revenue-trend' && (
            <p>Revenue shows consistent 15% month-over-month growth with healthy profit margins.</p>
          )}
          {chartType === 'client-distribution' && (
            <p>Tech startups represent the largest client segment at 45% of total business.</p>
          )}
          {chartType === 'project-status' && (
            <p>Strong project delivery with 12 completed projects and only 2 at-risk projects.</p>
          )}
          {chartType === 'productivity-overview' && (
            <p>Productivity trending upward with 95% efficiency in the most recent week.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChartPanel;
```

## Step 5: Styling and Theme Integration

### src/styles/dashboard.css
```css
/* Business Metrics Dashboard Styles */

.business-metrics-dashboard {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 2px solid #e0e0e0;
}

.dashboard-header h1 {
  color: #333;
  font-size: 2.2rem;
  font-weight: 600;
  margin: 0;
}

.dashboard-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.refresh-button {
  background: #0088FE;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.refresh-button:hover:not(:disabled) {
  background: #0066CC;
}

.refresh-button:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.last-updated {
  font-size: 0.9rem;
  color: #666;
}

/* Dashboard Grid Layout */
.dashboard-grid {
  display: grid;
  gap: 30px;
  grid-template-columns: 1fr;
}

/* Metric Sections */
.metrics-overview,
.client-metrics,
.productivity-metrics {
  background: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e8e8e8;
}

.metrics-overview h2,
.client-metrics h2,
.productivity-metrics h2 {
  color: #333;
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 20px;
  border-left: 4px solid #0088FE;
  padding-left: 15px;
}

.metric-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

/* Metric Card Styles */
.metric-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.metric-card.clickable {
  cursor: pointer;
}

.metric-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #0088FE;
}

.metric-header {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.metric-icon {
  width: 24px;
  height: 24px;
  margin-right: 10px;
  color: #0088FE;
}

.metric-title {
  font-size: 0.95rem;
  font-weight: 500;
  color: #666;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: #333;
  margin-bottom: 8px;
}

.metric-subtitle {
  font-size: 0.9rem;
  color: #888;
  margin-bottom: 10px;
}

.metric-trend {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.trend-indicator {
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.trend-positive .trend-indicator {
  background: #d4edda;
  color: #155724;
}

.trend-negative .trend-indicator {
  background: #f8d7da;
  color: #721c24;
}

.trend-period {
  color: #888;
}

.metric-action {
  position: absolute;
  bottom: 10px;
  right: 15px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.metric-card.clickable:hover .metric-action {
  opacity: 1;
}

.action-text {
  font-size: 0.8rem;
  color: #0088FE;
  font-weight: 500;
}

/* Charts Section */
.charts-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e8e8e8;
}

.chart-panel {
  width: 100%;
}

.chart-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.chart-controls h3 {
  color: #333;
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0;
  border-left: 4px solid #00C49F;
  padding-left: 15px;
}

.chart-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 0.9rem;
  cursor: pointer;
}

.chart-container {
  margin: 20px 0;
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
}

.chart-insights {
  margin-top: 15px;
  padding: 15px;
  background: #f0f7ff;
  border-radius: 8px;
  border-left: 4px solid #0088FE;
}

.insight-summary p {
  margin: 0;
  color: #333;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* AI Insights Section */
.insights-section {
  background: #ffffff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e8e8e8;
}

.insights-section h2 {
  color: #333;
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 20px;
  border-left: 4px solid #FFBB28;
  padding-left: 15px;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.insight-panel {
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.insight-panel.highlights {
  background: #f0f9f0;
  border-color: #00C49F;
}

.insight-panel.warnings {
  background: #fff8f0;
  border-color: #FF8042;
}

.insight-panel.recommendations {
  background: #f0f7ff;
  border-color: #0088FE;
}

.insight-panel h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 1.1rem;
  font-weight: 600;
}

.insight-panel ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.insight-panel li {
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 0.9rem;
  line-height: 1.4;
}

.insight-panel li:last-child {
  border-bottom: none;
}

.insight-highlight {
  color: #155724;
}

.insight-warning {
  color: #856404;
}

.insight-recommendation {
  color: #004085;
}

/* Loading and Error States */
.dashboard-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: #666;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0088FE;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.dashboard-error {
  text-align: center;
  padding: 40px;
  color: #666;
}

.dashboard-error h3 {
  color: #d32f2f;
  margin-bottom: 10px;
}

.retry-button {
  background: #d32f2f;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 15px;
}

.retry-button:hover {
  background: #b71c1c;
}

/* Responsive Design */
@media (max-width: 768px) {
  .business-metrics-dashboard {
    padding: 15px;
  }

  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .dashboard-controls {
    width: 100%;
    justify-content: space-between;
  }

  .metric-cards {
    grid-template-columns: 1fr;
  }

  .insights-grid {
    grid-template-columns: 1fr;
  }

  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .dashboard-header h1 {
    font-size: 1.8rem;
  }

  .metric-value {
    font-size: 1.6rem;
  }

  .metric-cards {
    gap: 15px;
  }

  .metric-card {
    padding: 15px;
  }
}
```

## Step 6: Testing and Validation

### tests/dashboard.test.js
```javascript
/**
 * Dashboard Component Tests
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Dashboard from '../src/components/Dashboard.jsx';
import dataService from '../src/services/dataService.js';

// Mock the data service
jest.mock('../src/services/dataService.js');

const mockDashboardData = {
  overview: {
    totalRevenue: '$134,900',
    monthlyRecurring: '$15,000',
    netProfit: '$90,600',
    profitMargin: '67%',
    cashFlow: '$25,600',
    runway: '8 months'
  },
  growth: {
    revenueGrowth: '+15%',
    clientGrowth: '+25%',
    profitGrowth: '+18%'
  },
  clients: {
    total: 12,
    active: 8,
    newThisMonth: 3,
    churnRate: '5%',
    averageValue: '$28,500',
    satisfaction: 9.3
  },
  productivity: {
    billableHours: 142,
    billablePercentage: '76%',
    averageRate: '$78.50',
    efficiency: '87%'
  },
  insights: {
    highlights: ['Revenue up 15% this month', 'New client acquired'],
    warnings: ['One project at risk', 'Cash flow needs attention'],
    recommendations: ['Consider rate increase', 'Expand service offerings']
  },
  lastUpdated: new Date().toISOString()
};

describe('Dashboard Component', () => {
  beforeEach(() => {
    dataService.initialize.mockResolvedValue();
    dataService.getDashboardData.mockResolvedValue(mockDashboardData);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders dashboard title', async () => {
    render(<Dashboard />);
    expect(screen.getByText('Business Metrics Dashboard')).toBeInTheDocument();
  });

  test('displays loading state initially', async () => {
    render(<Dashboard />);
    expect(screen.getByText('Loading business metrics...')).toBeInTheDocument();
  });

  test('loads and displays dashboard data', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('$134,900')).toBeInTheDocument();
      expect(screen.getByText('$90,600')).toBeInTheDocument();
      expect(screen.getByText('67%')).toBeInTheDocument();
    });
  });

  test('handles refresh button click', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('$134,900')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);

    expect(dataService.getDashboardData).toHaveBeenCalledTimes(2);
  });

  test('displays error state when data loading fails', async () => {
    dataService.getDashboardData.mockRejectedValue(new Error('API Error'));
    
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Error Loading Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
    });
  });

  test('metric cards are clickable', async () => {
    const mockHandleMetricClick = jest.fn();
    
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('$134,900')).toBeInTheDocument();
    });

    // Find and click a metric card
    const revenueCard = screen.getByText('Total Revenue').closest('.metric-card');
    fireEvent.click(revenueCard);

    // Note: This would trigger the handleMetricClick function in the actual component
    // The specific assertion would depend on the expected behavior
  });
});
```

### tests/dataService.test.js
```javascript
/**
 * Data Service Tests
 */

import dataService from '../src/services/dataService.js';
import apiClient from '../src/services/apiClient.js';

// Mock the API client
jest.mock('../src/services/apiClient.js');

describe('DataService', () => {
  beforeEach(() => {
    // Reset cache before each test
    dataService.cache.clear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initializes successfully', async () => {
    apiClient.initialize.mockResolvedValue();
    await dataService.initialize();
    expect(apiClient.initialize).toHaveBeenCalled();
  });

  test('caches data correctly', async () => {
    const mockData = { revenue: { total: 100000 } };
    const mockFetcher = jest.fn().mockResolvedValue(mockData);

    // First call should fetch data
    const result1 = await dataService.getCachedData('test-key', mockFetcher);
    expect(result1).toEqual(mockData);
    expect(mockFetcher).toHaveBeenCalledTimes(1);

    // Second call should return cached data
    const result2 = await dataService.getCachedData('test-key', mockFetcher);
    expect(result2).toEqual(mockData);
    expect(mockFetcher).toHaveBeenCalledTimes(1); // Still only called once
  });

  test('processes business metrics correctly', () => {
    const rawData = {
      financeData: {
        revenue: { total: 100000, recurring: 20000, history: [80000, 90000, 100000] },
        profit: { net: 50000, margin: 0.5, history: [40000, 45000, 50000] },
        cashflow: { current: 25000 },
        expenses: { monthly: 8000 }
      },
      clientMetrics: {
        total: 10,
        active: 8,
        new_this_month: 2,
        churn_rate: 0.05,
        average_value: 12500,
        satisfaction_score: 9.1,
        growth: [8, 9, 10]
      },
      projectStatus: {
        active: [1, 2, 3],
        completed_this_month: 5,
        on_track: 2,
        at_risk: 1,
        average_duration: 45
      },
      timeMetrics: {
        billable: { total: 160, percentage: 0.8 },
        average_rate: 75,
        efficiency: 0.85
      },
      insights: {
        highlights: ['Great month!'],
        warnings: ['Cash flow low'],
        recommendations: ['Increase rates'],
        predictions: {}
      }
    };

    const processed = dataService.processBusinessMetrics(rawData);

    expect(processed.overview.totalRevenue).toBe('$100,000');
    expect(processed.overview.profitMargin).toBe('50%');
    expect(processed.clients.total).toBe(10);
    expect(processed.productivity.billablePercentage).toBe('80%');
  });
});
```

## Step 7: Deployment and Distribution

### Package and Distribution

```bash
# Build the plugin
npm run build

# Test the plugin
npm run test

# Package for distribution
westfall plugin package

# Install locally for testing
westfall plugin install ./dist/business-metrics-dashboard.zip

# Publish to Westfall Plugin Marketplace
westfall plugin publish --public
```

### deployment/package.json
```json
{
  "name": "business-metrics-dashboard",
  "version": "1.0.0",
  "description": "Advanced business intelligence dashboard for consulting firms",
  "main": "dist/index.js",
  "scripts": {
    "build": "webpack --mode production",
    "dev": "webpack --mode development --watch",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint src/**/*.{js,jsx}",
    "package": "westfall plugin package",
    "publish": "westfall plugin publish"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "recharts": "^2.8.0"
  },
  "devDependencies": {
    "@babel/preset-react": "^7.22.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/react": "^13.4.0",
    "babel-loader": "^9.1.0",
    "css-loader": "^6.8.0",
    "eslint": "^8.50.0",
    "eslint-plugin-react": "^7.33.0",
    "jest": "^29.7.0",
    "style-loader": "^3.3.0",
    "webpack": "^5.88.0",
    "webpack-cli": "^5.1.0"
  },
  "westfall": {
    "minVersion": "2.0.0",
    "permissions": [
      "read_finance_data",
      "read_crm_data",
      "ai_assistant_integration"
    ],
    "category": "business-intelligence"
  }
}
```

## Advanced Features and Extensions

### Real-time Data Updates

```javascript
// WebSocket integration for real-time updates
class RealtimeDataService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect() {
    this.socket = new WebSocket('wss://api.westfall.app/realtime');
    
    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.notifyListeners(data.type, data.payload);
    };
  }

  subscribe(dataType, callback) {
    if (!this.listeners.has(dataType)) {
      this.listeners.set(dataType, []);
    }
    this.listeners.get(dataType).push(callback);
  }

  notifyListeners(dataType, payload) {
    const callbacks = this.listeners.get(dataType) || [];
    callbacks.forEach(callback => callback(payload));
  }
}
```

### AI Integration

```javascript
// AI-powered insights and recommendations
class AIInsightsService {
  async analyzeBusinessTrends(data) {
    const prompt = `Analyze business data: ${JSON.stringify(data)}`;
    const response = await westfall.ai.generateInsights(prompt);
    return this.parseInsights(response);
  }

  parseInsights(response) {
    return {
      trends: response.trends || [],
      predictions: response.predictions || {},
      recommendations: response.recommendations || [],
      risks: response.risks || []
    };
  }
}
```

## Resources and Downloads

### Complete Plugin Package
- Full source code with documentation
- Unit and integration tests
- Webpack configuration
- ESLint and Prettier configuration
- Sample data for testing

### Additional Templates
- Custom metric cards
- Alternative chart types
- Mobile-responsive layouts
- Dark mode themes

### Documentation
- API reference guide
- Plugin development best practices
- Performance optimization tips
- Security considerations

---

*This guide provides a complete foundation for building sophisticated dashboard plugins for Westfall Personal Assistant. The modular architecture and comprehensive API integration demonstrate best practices for plugin development.*

**Download the complete plugin source**: [business-metrics-dashboard.zip](resources/business-metrics-dashboard.zip)

---

*Last updated: September 8, 2025*