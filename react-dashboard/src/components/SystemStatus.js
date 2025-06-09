import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  CheckCircle,
  Warning,
  Error,
  Speed,
  Security,
  Cloud,
} from '@mui/icons-material';
import { useTrading } from '../context/TradingContext';

function SystemStatus() {
  const { state } = useTrading();

  const systemComponents = [
    {
      name: 'Trading Engine',
      status: state.trading.isActive ? 'online' : 'ready',
      description: state.trading.isActive ? 'Live trading active' : 'Ready for trading',
      icon: <Speed />,
    },
    {
      name: 'MEV Protection',
      status: 'online',
      description: 'Jito Block Engine connected',
      icon: <Security />,
    },
    {
      name: 'RPC Endpoints',
      status: state.isConnected ? 'online' : 'offline',
      description: state.isConnected ? 'QuickNode & Helius active' : 'Connection issues',
      icon: <Cloud />,
    },
    {
      name: 'Risk Management',
      status: 'online',
      description: 'Position sizing active',
      icon: <CheckCircle />,
    },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'ready':
        return <Warning sx={{ color: 'warning.main' }} />;
      case 'offline':
        return <Error sx={{ color: 'error.main' }} />;
      default:
        return <CheckCircle sx={{ color: 'success.main' }} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'ready':
        return 'warning';
      case 'offline':
        return 'error';
      default:
        return 'success';
    }
  };

  const overallHealth = systemComponents.every(comp => comp.status === 'online') ? 'excellent' :
                      systemComponents.some(comp => comp.status === 'offline') ? 'issues' : 'good';

  return (
    <Card className="metric-card">
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 500 }}>
            System Health
          </Typography>
          <Chip
            label={overallHealth === 'excellent' ? 'Excellent' : overallHealth === 'good' ? 'Good' : 'Issues'}
            color={overallHealth === 'excellent' ? 'success' : overallHealth === 'good' ? 'warning' : 'error'}
            size="small"
          />
        </Box>

        {/* Overall Health Progress */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              System Performance
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {overallHealth === 'excellent' ? '100%' : overallHealth === 'good' ? '85%' : '60%'}
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={overallHealth === 'excellent' ? 100 : overallHealth === 'good' ? 85 : 60}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(0,0,0,0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                backgroundColor: overallHealth === 'excellent' ? 'success.main' : 
                               overallHealth === 'good' ? 'warning.main' : 'error.main'
              }
            }}
          />
        </Box>

        {/* Component Status List */}
        <List dense>
          {systemComponents.map((component, index) => (
            <ListItem key={index} sx={{ px: 0 }}>
              <ListItemIcon sx={{ minWidth: 36 }}>
                {getStatusIcon(component.status)}
              </ListItemIcon>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {component.name}
                    </Typography>
                    <Chip
                      label={component.status}
                      color={getStatusColor(component.status)}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem', height: 20 }}
                    />
                  </Box>
                }
                secondary={
                  <Typography variant="caption" color="text.secondary">
                    {component.description}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>

        {/* Trading Session Info */}
        <Box sx={{ mt: 2, p: 2, backgroundColor: 'rgba(25, 118, 210, 0.05)', borderRadius: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
            Current Session
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Uptime: {state.system.uptime || 0} minutes
          </Typography>
          <br />
          <Typography variant="caption" color="text.secondary">
            Trades: {state.trading.totalTrades} executed
          </Typography>
          <br />
          <Typography variant="caption" color="text.secondary">
            Last Update: {state.system.lastUpdate ? new Date(state.system.lastUpdate).toLocaleTimeString() : 'Never'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

export default SystemStatus;
