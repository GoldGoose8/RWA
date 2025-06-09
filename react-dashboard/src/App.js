import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography, Box } from '@mui/material';
import Dashboard from './components/Dashboard';
import TradingView from './components/TradingView';
import SystemHealth from './components/SystemHealth';
import Navigation from './components/Navigation';
import { TradingProvider } from './context/TradingContext';

function App() {
  return (
    <TradingProvider>
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static" sx={{
            background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
            boxShadow: '0 4px 20px rgba(25, 118, 210, 0.3)',
            borderRadius: 0
          }}>
            <Toolbar sx={{ py: 1 }}>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h5" component="div" sx={{ fontWeight: 700, mb: 0.5 }}>
                  Williams Capital Management
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Quantitative Trading Platform • Real-time Portfolio Management
                </Typography>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="body2" sx={{ opacity: 0.9, mb: 0.5 }}>
                  Winsor Williams II
                </Typography>
                <Typography variant="caption" sx={{
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  fontWeight: 500
                }}>
                  Fund Manager
                </Typography>
              </Box>
            </Toolbar>
          </AppBar>
          
          <Navigation />
          
          <Container maxWidth="xl" sx={{ mt: 2, mb: 2 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/trading" element={<TradingView />} />
              <Route path="/health" element={<SystemHealth />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </TradingProvider>
  );
}

export default App;
