import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Typography,
  Box,
} from '@mui/material';

// Mock trades data
const mockTrades = [
  {
    id: 1,
    time: '18:33:56',
    action: 'BUY',
    pair: 'SOL-USDC',
    amount: '7.558 SOL',
    price: '$152.60',
    status: 'Failed',
    reason: 'Insufficient USDC'
  },
  {
    id: 2,
    time: '18:25:12',
    action: 'SELL',
    pair: 'SOL-USDC',
    amount: '2.150 SOL',
    price: '$152.45',
    status: 'Completed',
    pnl: '+$12.50'
  },
  {
    id: 3,
    time: '18:18:33',
    action: 'BUY',
    pair: 'SOL-USDC',
    amount: '1.875 SOL',
    price: '$151.80',
    status: 'Completed',
    pnl: '+$8.25'
  },
];

function RecentTrades({ trades = mockTrades }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'Completed':
        return 'success';
      case 'Failed':
        return 'error';
      case 'Pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getActionColor = (action) => {
    return action === 'BUY' ? 'primary' : 'secondary';
  };

  if (!trades || trades.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          No recent trades available
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Time</TableCell>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Action</TableCell>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Pair</TableCell>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Amount</TableCell>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Price</TableCell>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Status</TableCell>
            <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>P&L</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {trades.map((trade) => (
            <TableRow 
              key={trade.id}
              sx={{ 
                '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
                '&:last-child td, &:last-child th': { border: 0 }
              }}
            >
              <TableCell sx={{ fontSize: '0.875rem' }}>
                {trade.time}
              </TableCell>
              <TableCell>
                <Chip
                  label={trade.action}
                  color={getActionColor(trade.action)}
                  size="small"
                  variant="outlined"
                  sx={{ fontWeight: 600, fontSize: '0.75rem' }}
                />
              </TableCell>
              <TableCell sx={{ fontSize: '0.875rem', fontWeight: 500 }}>
                {trade.pair}
              </TableCell>
              <TableCell sx={{ fontSize: '0.875rem' }}>
                {trade.amount}
              </TableCell>
              <TableCell sx={{ fontSize: '0.875rem' }}>
                {trade.price}
              </TableCell>
              <TableCell>
                <Chip
                  label={trade.status}
                  color={getStatusColor(trade.status)}
                  size="small"
                  sx={{ fontSize: '0.75rem' }}
                />
              </TableCell>
              <TableCell sx={{ fontSize: '0.875rem' }}>
                {trade.pnl ? (
                  <Typography
                    variant="body2"
                    sx={{
                      color: trade.pnl.startsWith('+') ? 'success.main' : 'error.main',
                      fontWeight: 600
                    }}
                  >
                    {trade.pnl}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    {trade.reason || '-'}
                  </Typography>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default RecentTrades;
