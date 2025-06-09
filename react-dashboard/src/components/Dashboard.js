import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Paper,
  Divider,
} from '@mui/material';
import {
  AccountBalance,
  TrendingUp,
  Assessment,
  Security,
  Timeline,
  PieChart,
} from '@mui/icons-material';
import { useTrading } from '../context/TradingContext';
import MetricCard from './MetricCard';
import TradingChart from './TradingChart';
import RecentTrades from './RecentTrades';
import SystemStatus from './SystemStatus';

function Dashboard() {
  const { state, isLoading } = useTrading();

  if (isLoading) {
    return (
      <Box sx={{ width: '100%', mt: 4 }}>
        <LinearProgress color="primary" sx={{ borderRadius: 2, height: 6 }} />
        <Typography variant="h6" sx={{ textAlign: 'center', mt: 3, color: 'text.secondary' }}>
          Connecting to Trading Platform...
        </Typography>
        <Typography variant="body2" sx={{ textAlign: 'center', mt: 1, color: 'text.secondary' }}>
          Establishing secure connection to quantitative trading systems
        </Typography>
      </Box>
    );
  }

  const formatCurrency = (value, currency = 'SOL', decimals = 4) => {
    return `${value.toFixed(decimals)} ${currency}`;
  };

  const formatPercentage = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Executive Summary Header */}
      <Paper className="hedge-fund-header" sx={{ mb: 4 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={8}>
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
              Portfolio Overview
            </Typography>
            <Typography variant="h6" sx={{ opacity: 0.9, mb: 2 }}>
              Real-time quantitative trading performance and risk metrics
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip
                label="Live Trading Active"
                color="success"
                variant="outlined"
                sx={{ backgroundColor: 'rgba(255,255,255,0.1)', color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
              />
              <Chip
                label="MEV Protected"
                variant="outlined"
                sx={{ backgroundColor: 'rgba(255,255,255,0.1)', color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
              />
              <Chip
                label="Risk Managed"
                variant="outlined"
                sx={{ backgroundColor: 'rgba(255,255,255,0.1)', color: 'white', borderColor: 'rgba(255,255,255,0.3)' }}
              />
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <Box className="performance-metric">
              <Typography className="metric-value" sx={{ color: 'white' }}>
                {formatCurrency(state.wallet.balance, 'SOL', 2)}
              </Typography>
              <Typography className="metric-label" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                Total Portfolio Value
              </Typography>
              <Typography variant="h6" sx={{ color: 'rgba(255,255,255,0.9)', mt: 1 }}>
                ${state.wallet.balanceUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Key Performance Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Assets Under Management"
            value={formatCurrency(state.wallet.balance, 'SOL', 3)}
            subtitle={`$${state.wallet.balanceUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            icon={<AccountBalance />}
            color="primary"
            trend={state.market.solChange24h}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Net Performance"
            value={formatCurrency(state.trading.totalPnL, 'SOL', 4)}
            subtitle={`$${state.trading.totalPnLUSD.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
            icon={<TrendingUp />}
            color={state.trading.totalPnL >= 0 ? 'success' : 'error'}
            trend={state.trading.totalPnL}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Strategy Success Rate"
            value={`${state.trading.winRate.toFixed(1)}%`}
            subtitle={`${state.trading.successfulTrades} of ${state.trading.totalTrades} positions`}
            icon={<Assessment />}
            color={state.trading.winRate >= 60 ? 'success' : state.trading.winRate >= 40 ? 'warning' : 'error'}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Market Price (SOL)"
            value={`$${state.market.solPrice.toFixed(2)}`}
            subtitle={`${formatPercentage(state.market.solChange24h)} (24h)`}
            icon={<Timeline />}
            color={state.market.solChange24h >= 0 ? 'success' : 'error'}
            trend={state.market.solChange24h}
          />
        </Grid>
      </Grid>

      {/* Main Content Row */}
      <Grid container spacing={3}>
        {/* Trading Chart */}
        <Grid item xs={12} lg={8}>
          <Card className="metric-card">
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 500 }}>
                  Performance Chart
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip
                    label={state.trading.isActive ? 'Trading Active' : 'Trading Paused'}
                    color={state.trading.isActive ? 'success' : 'warning'}
                    size="small"
                  />
                  <Chip
                    label="MEV Protected"
                    color="primary"
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>
              <TradingChart />
            </CardContent>
          </Card>
        </Grid>

        {/* System Status */}
        <Grid item xs={12} lg={4}>
          <SystemStatus />
        </Grid>

        {/* Recent Trades */}
        <Grid item xs={12}>
          <Card className="metric-card">
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
                Recent Trades
              </Typography>
              <RecentTrades trades={state.recentTrades} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Trading Status Banner */}
      {state.trading.isActive && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 20,
            right: 20,
            backgroundColor: 'rgba(0, 255, 136, 0.1)',
            border: '1px solid rgba(0, 255, 136, 0.3)',
            borderRadius: 2,
            p: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            zIndex: 1000,
          }}
        >
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: '#00ff88',
              animation: 'pulse 2s infinite',
            }}
          />
          <Typography variant="body2" sx={{ color: '#00ff88', fontWeight: 500 }}>
            Live Trading Active
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default Dashboard;
