import React from 'react';
import { Box, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock data for demonstration
const mockData = [
  { time: '09:00', value: 15.553, pnl: 0 },
  { time: '09:30', value: 15.558, pnl: 0.005 },
  { time: '10:00', value: 15.545, pnl: -0.008 },
  { time: '10:30', value: 15.562, pnl: 0.009 },
  { time: '11:00', value: 15.571, pnl: 0.018 },
  { time: '11:30', value: 15.568, pnl: 0.015 },
  { time: '12:00', value: 15.553, pnl: 0 },
];

function TradingChart() {
  return (
    <Box sx={{ width: '100%', height: 400 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={mockData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis 
            dataKey="time" 
            stroke="#757575"
            fontSize={12}
          />
          <YAxis 
            stroke="#757575"
            fontSize={12}
            domain={['dataMin - 0.01', 'dataMax + 0.01']}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
            }}
            formatter={(value, name) => [
              `${value.toFixed(4)} SOL`,
              name === 'value' ? 'Portfolio Value' : 'P&L'
            ]}
          />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#1976d2" 
            strokeWidth={3}
            dot={{ fill: '#1976d2', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#1976d2', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
}

export default TradingChart;
