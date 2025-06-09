import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Box,
  Tabs,
  Tab,
  Chip,
  useTheme
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  TrendingUp as TradingIcon,
  MonitorHeart as HealthIcon,
} from '@mui/icons-material';
import { useTrading } from '../context/TradingContext';

function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();
  const { state } = useTrading();

  const tabs = [
    {
      label: 'Portfolio Overview',
      value: '/',
      icon: <DashboardIcon />,
    },
    {
      label: 'Trading Operations',
      value: '/trading',
      icon: <TradingIcon />,
    },
    {
      label: 'System Status',
      value: '/health',
      icon: <HealthIcon />,
    },
  ];

  const handleTabChange = (event, newValue) => {
    navigate(newValue);
  };

  const getStatusColor = () => {
    if (!state.isConnected) return 'error';
    if (state.system.health === 'healthy') return 'success';
    if (state.system.health === 'unhealthy') return 'warning';
    return 'default';
  };

  const getStatusText = () => {
    if (!state.isConnected) return 'Offline';
    if (state.trading.isActive) return 'Live Trading';
    if (state.system.health === 'healthy') return 'Ready';
    return 'Maintenance';
  };

  return (
    <Box sx={{
      borderBottom: 1,
      borderColor: 'divider',
      backgroundColor: 'background.paper',
      px: 3,
      py: 1,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <Tabs 
        value={location.pathname} 
        onChange={handleTabChange}
        sx={{
          '& .MuiTab-root': {
            color: 'text.secondary',
            fontWeight: 500,
            '&.Mui-selected': {
              color: theme.palette.primary.main,
              fontWeight: 600,
            },
          },
          '& .MuiTabs-indicator': {
            backgroundColor: theme.palette.primary.main,
            height: 3,
            borderRadius: '2px 2px 0 0',
          },
        }}
      >
        {tabs.map((tab) => (
          <Tab
            key={tab.value}
            label={tab.label}
            value={tab.value}
            icon={tab.icon}
            iconPosition="start"
            sx={{ 
              minHeight: 48,
              textTransform: 'none',
              fontSize: '0.9rem',
            }}
          />
        ))}
      </Tabs>

      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        {/* Connection Status */}
        <Chip
          label={getStatusText()}
          color={getStatusColor()}
          size="small"
          variant="outlined"
          sx={{
            fontWeight: 500,
            '& .MuiChip-label': {
              px: 1,
            },
          }}
        />

        {/* Live indicator */}
        {state.isConnected && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: state.trading.isActive ? '#00ff88' : '#ffaa00',
                animation: 'pulse 2s infinite',
              }}
            />
            <Box sx={{ fontSize: '0.8rem', color: '#cccccc' }}>
              {state.trading.isActive ? 'LIVE' : 'READY'}
            </Box>
          </Box>
        )}

        {/* Portfolio Value */}
        {state.wallet.balance > 0 && (
          <Chip
            label={`${state.wallet.balance.toFixed(3)} SOL`}
            color="primary"
            size="small"
            variant="outlined"
            sx={{
              fontWeight: 600,
              backgroundColor: 'rgba(25, 118, 210, 0.1)',
              borderColor: theme.palette.primary.main,
            }}
          />
        )}
      </Box>
    </Box>
  );
}

export default Navigation;
