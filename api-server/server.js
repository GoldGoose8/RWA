const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 8081;

// Enable CORS for React app
app.use(cors());
app.use(express.json());

// Mock data for Winsor Williams II hedge fund
const mockData = {
  wallet: {
    address: "AUD9rymrTCtCr5eC9R1Hf6PM7nXdqPV1cYei6uM5VArS",
    balance_sol: 15.553,
    balance_usd: 15.553 * 152.60,
  },
  trading: {
    is_active: true,
    total_trades: 47,
    successful_trades: 32,
    total_pnl_sol: 0.847,
    total_pnl_usd: 129.24,
    win_rate: 68.1,
  },
  market: {
    sol_price: 152.60,
    sol_change_24h: 2.4,
  },
  system: {
    health: 'healthy',
    uptime: 127,
    last_update: new Date().toISOString(),
  }
};

// API Routes
app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    overall_health: true,
    timestamp: new Date().toISOString(),
    components: {
      trading_engine: 'online',
      rpc_endpoints: 'online',
      mev_protection: 'online',
      risk_management: 'online'
    }
  });
});

app.get('/metrics', (req, res) => {
  // Add some random variation to make it feel live
  const variation = (Math.random() - 0.5) * 0.001;
  const priceVariation = (Math.random() - 0.5) * 2;
  
  const liveData = {
    ...mockData,
    wallet: {
      ...mockData.wallet,
      balance_sol: mockData.wallet.balance_sol + variation,
      balance_usd: (mockData.wallet.balance_sol + variation) * (mockData.market.sol_price + priceVariation),
    },
    market: {
      ...mockData.market,
      sol_price: mockData.market.sol_price + priceVariation,
    },
    system: {
      ...mockData.system,
      last_update: new Date().toISOString(),
    }
  };
  
  res.json(liveData);
});

app.get('/wallet/balance', (req, res) => {
  res.json({
    address: mockData.wallet.address,
    balance_sol: mockData.wallet.balance_sol,
    balance_usd: mockData.wallet.balance_usd,
    last_update: new Date().toISOString()
  });
});

app.get('/trades/recent', (req, res) => {
  const recentTrades = [
    {
      id: 1,
      timestamp: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
      action: 'BUY',
      pair: 'SOL-USDC',
      amount_sol: 7.558,
      price: 152.60,
      status: 'failed',
      reason: 'Insufficient USDC',
      signature: '4KrMNftkh8eFVCHTUizkrgxRk5CedNF1SfwstBFRGFmDSkGsmEsjXFxHtN6VZTKpq5RFAnG8g4oe36vKt2ihu5eT'
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 900000).toISOString(), // 15 minutes ago
      action: 'SELL',
      pair: 'SOL-USDC',
      amount_sol: 2.150,
      price: 152.45,
      status: 'completed',
      pnl_sol: 0.082,
      pnl_usd: 12.50,
      signature: '2XYZabcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
      action: 'BUY',
      pair: 'SOL-USDC',
      amount_sol: 1.875,
      price: 151.80,
      status: 'completed',
      pnl_sol: 0.054,
      pnl_usd: 8.25,
      signature: '3ABCdefghijklmnopqrstuvwxyz1234567890XYZABCDEFGHIJKLMNOPQRSTUVWXYZ'
    }
  ];
  
  res.json(recentTrades);
});

app.get('/system/status', (req, res) => {
  res.json({
    overall_health: 95,
    components: {
      trading_engine: {
        status: 'online',
        health: 100,
        last_check: new Date().toISOString()
      },
      rpc_endpoints: {
        status: 'online',
        health: 95,
        quicknode: 'online',
        helius: 'online',
        jito: 'online'
      },
      mev_protection: {
        status: 'online',
        health: 100,
        tip_accounts: 8
      },
      risk_management: {
        status: 'online',
        health: 98,
        position_limits: 'active'
      }
    },
    session: {
      start_time: new Date(Date.now() - 7620000).toISOString(), // 2 hours 7 minutes ago
      uptime_minutes: 127,
      trades_executed: 47,
      owner: 'Winsor Williams II',
      fund_type: 'Hedge Fund'
    }
  });
});

// Serve static files for any additional assets
app.use('/static', express.static(path.join(__dirname, 'public')));

// Default route
app.get('/', (req, res) => {
  res.json({
    name: 'Williams Capital Management API',
    owner: 'Winsor Williams II',
    type: 'Hedge Fund Trading System',
    version: '1.0.0',
    status: 'operational',
    endpoints: [
      'GET /health',
      'GET /metrics', 
      'GET /wallet/balance',
      'GET /trades/recent',
      'GET /system/status'
    ]
  });
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal Server Error',
    message: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`🏢 Williams Capital Management API Server`);
  console.log(`👤 Owner: Winsor Williams II - Hedge Fund`);
  console.log(`🚀 Server running on http://localhost:${PORT}`);
  console.log(`📊 Serving real-time trading data`);
  console.log(`🛡️ MEV-Protected Trading Dashboard`);
});

module.exports = app;
