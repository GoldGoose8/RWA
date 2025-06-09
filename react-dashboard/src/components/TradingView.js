import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  PlayArrow,
  Pause,
  Settings,
  TrendingUp,
} from '@mui/icons-material';
import { useTrading } from '../context/TradingContext';

function TradingView() {
  const { state } = useTrading();

  const strategies = [
    {
      name: 'Opportunistic Volatility Breakout',
      status: 'Active',
      allocation: '100%',
      performance: '+1.2%',
      trades: 15,
    },
    {
      name: 'Mean Reversion',
      status: 'Standby',
      allocation: '0%',
      performance: '+0.8%',
      trades: 8,
    },
    {
      name: 'Momentum SOL-USDC',
      status: 'Standby',
      allocation: '0%',
      performance: '+0.5%',
      trades: 12,
    },
  ];

  const positions = [
    {
      pair: 'SOL-USDC',
      side: 'Long',
      size: '15.553 SOL',
      entryPrice: '$151.80',
      currentPrice: '$152.60',
      pnl: '+$12.46',
      pnlPercent: '+0.52%',
    },
  ];

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Trading Operations
        </Typography>
        <Typography variant="body1" sx={{ color: 'text.secondary' }}>
          Real-time trading strategy management and execution control
        </Typography>
      </Box>

      {/* Trading Controls */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
                Trading Control
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Button
                  variant={state.trading.isActive ? "outlined" : "contained"}
                  color={state.trading.isActive ? "error" : "success"}
                  startIcon={state.trading.isActive ? <Pause /> : <PlayArrow />}
                  size="large"
                >
                  {state.trading.isActive ? 'Pause Trading' : 'Start Trading'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Settings />}
                  size="large"
                >
                  Settings
                </Button>
              </Box>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={state.trading.isActive ? 'Live Trading' : 'Trading Paused'}
                  color={state.trading.isActive ? 'success' : 'warning'}
                  variant="outlined"
                />
                <Chip
                  label="MEV Protected"
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label="Risk Managed"
                  color="info"
                  variant="outlined"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
                Session Performance
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Total P&L
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'success.main' }}>
                    +{state.trading.totalPnL.toFixed(4)} SOL
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Win Rate
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {state.trading.winRate.toFixed(1)}%
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Active Strategies */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
                Trading Strategies
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Strategy</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Allocation</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Performance</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Trades</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {strategies.map((strategy, index) => (
                      <TableRow key={index}>
                        <TableCell sx={{ fontWeight: 500 }}>
                          {strategy.name}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={strategy.status}
                            color={strategy.status === 'Active' ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{strategy.allocation}</TableCell>
                        <TableCell>
                          <Typography
                            variant="body2"
                            sx={{
                              color: strategy.performance.startsWith('+') ? 'success.main' : 'error.main',
                              fontWeight: 600
                            }}
                          >
                            {strategy.performance}
                          </Typography>
                        </TableCell>
                        <TableCell>{strategy.trades}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Current Positions */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 500, mb: 2 }}>
                Current Positions
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Pair</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Side</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Size</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Entry Price</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Current Price</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>P&L</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {positions.map((position, index) => (
                      <TableRow key={index}>
                        <TableCell sx={{ fontWeight: 500 }}>
                          {position.pair}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={position.side}
                            color={position.side === 'Long' ? 'success' : 'error'}
                            size="small"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>{position.size}</TableCell>
                        <TableCell>{position.entryPrice}</TableCell>
                        <TableCell>{position.currentPrice}</TableCell>
                        <TableCell>
                          <Box>
                            <Typography
                              variant="body2"
                              sx={{
                                color: position.pnl.startsWith('+') ? 'success.main' : 'error.main',
                                fontWeight: 600
                              }}
                            >
                              {position.pnl}
                            </Typography>
                            <Typography
                              variant="caption"
                              sx={{
                                color: position.pnlPercent.startsWith('+') ? 'success.main' : 'error.main'
                              }}
                            >
                              {position.pnlPercent}
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default TradingView;
