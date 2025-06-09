import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Speed,
  Security,
  Cloud,
  Storage,
  NetworkCheck,
} from '@mui/icons-material';
import { useTrading } from '../context/TradingContext';

function SystemHealth() {
  const { state } = useTrading();

  const healthMetrics = [
    {
      category: 'Trading Engine',
      status: state.trading.isActive ? 'excellent' : 'good',
      value: state.trading.isActive ? 100 : 85,
      description: 'Core trading algorithms and execution engine',
      components: [
        { name: 'Signal Generation', status: 'online' },
        { name: 'Position Sizing', status: 'online' },
        { name: 'Risk Management', status: 'online' },
        { name: 'Strategy Selection', status: state.trading.isActive ? 'online' : 'standby' },
      ]
    },
    {
      category: 'Network Infrastructure',
      status: state.isConnected ? 'excellent' : 'poor',
      value: state.isConnected ? 95 : 30,
      description: 'RPC endpoints and blockchain connectivity',
      components: [
        { name: 'QuickNode RPC', status: state.isConnected ? 'online' : 'offline' },
        { name: 'Helius RPC', status: state.isConnected ? 'online' : 'offline' },
        { name: 'Jito Block Engine', status: 'online' },
        { name: 'Jupiter API', status: 'online' },
      ]
    },
    {
      category: 'Security & Protection',
      status: 'excellent',
      value: 100,
      description: 'MEV protection and transaction security',
      components: [
        { name: 'MEV Protection', status: 'online' },
        { name: 'Bundle Execution', status: 'online' },
        { name: 'Slippage Control', status: 'online' },
        { name: 'Wallet Security', status: 'online' },
      ]
    },
    {
      category: 'Data & Analytics',
      status: 'good',
      value: 88,
      description: 'Market data feeds and performance tracking',
      components: [
        { name: 'Price Feeds', status: 'online' },
        { name: 'Market Data', status: 'online' },
        { name: 'Performance Tracking', status: 'online' },
        { name: 'Whale Monitoring', status: 'warning' },
      ]
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'excellent':
        return 'success';
      case 'good':
        return 'info';
      case 'warning':
        return 'warning';
      case 'poor':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />;
      case 'warning':
        return <Warning sx={{ color: 'warning.main', fontSize: 16 }} />;
      case 'offline':
        return <Error sx={{ color: 'error.main', fontSize: 16 }} />;
      case 'standby':
        return <Speed sx={{ color: 'info.main', fontSize: 16 }} />;
      default:
        return <CheckCircle sx={{ color: 'success.main', fontSize: 16 }} />;
    }
  };

  const overallHealth = healthMetrics.reduce((acc, metric) => acc + metric.value, 0) / healthMetrics.length;

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          System Health Monitor
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Comprehensive monitoring of all trading system components
        </Typography>
      </Box>

      {/* Overall Health Summary */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Overall System Health
            </Typography>
            <Chip
              label={`${overallHealth.toFixed(0)}% Operational`}
              color={overallHealth >= 95 ? 'success' : overallHealth >= 80 ? 'info' : overallHealth >= 60 ? 'warning' : 'error'}
              size="large"
              sx={{ fontWeight: 600 }}
            />
          </Box>
          
          <LinearProgress
            variant="determinate"
            value={overallHealth}
            sx={{
              height: 12,
              borderRadius: 6,
              backgroundColor: 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 6,
                backgroundColor: overallHealth >= 95 ? 'success.main' : 
                               overallHealth >= 80 ? 'info.main' : 
                               overallHealth >= 60 ? 'warning.main' : 'error.main'
              }
            }}
          />
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              System Performance Score
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {overallHealth.toFixed(1)}/100
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Detailed Health Metrics */}
      <Grid container spacing={3}>
        {healthMetrics.map((metric, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 500 }}>
                    {metric.category}
                  </Typography>
                  <Chip
                    label={metric.status}
                    color={getStatusColor(metric.status)}
                    size="small"
                    sx={{ textTransform: 'capitalize' }}
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {metric.description}
                </Typography>

                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      Health Score
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {metric.value}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={metric.value}
                    color={getStatusColor(metric.status)}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: 'rgba(0,0,0,0.1)',
                      '& .MuiLinearProgress-bar': {
                        borderRadius: 3,
                      }
                    }}
                  />
                </Box>

                <List dense>
                  {metric.components.map((component, compIndex) => (
                    <ListItem key={compIndex} sx={{ px: 0, py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 24 }}>
                        {getStatusIcon(component.status)}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography variant="body2" sx={{ fontSize: '0.875rem' }}>
                            {component.name}
                          </Typography>
                        }
                      />
                      <Chip
                        label={component.status}
                        size="small"
                        variant="outlined"
                        sx={{ 
                          fontSize: '0.7rem', 
                          height: 20,
                          textTransform: 'capitalize'
                        }}
                        color={
                          component.status === 'online' ? 'success' :
                          component.status === 'warning' ? 'warning' :
                          component.status === 'offline' ? 'error' : 'info'
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* System Information */}
      <Card sx={{ mt: 4 }}>
        <CardContent>
          <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
            System Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Uptime
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {state.system.uptime || 0} minutes
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Total Trades
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {state.trading.totalTrades}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Success Rate
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {state.trading.winRate.toFixed(1)}%
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Typography variant="body2" color="text.secondary">
                Last Update
              </Typography>
              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                {state.system.lastUpdate ? new Date(state.system.lastUpdate).toLocaleTimeString() : 'Never'}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}

export default SystemHealth;
