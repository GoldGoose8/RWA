# Enhanced Dashboard System - Williams Capital Management

## 🚀 Live Trading Integration Dashboard

Professional trading dashboard with real-time integration to the live trading system, designed for **Winsor Williams II** hedge fund operations.

### ✨ Key Features

- **🔄 Real-time Updates:** Metrics refresh every 30 seconds, synchronized with live trading system
- **💰 Live Wallet Tracking:** Real-time SOL balance and USD value from blockchain
- **📊 Trading Metrics:** Live trading session data, P&L, win rates, and trade history
- **🛡️ MEV Protection Status:** Real-time monitoring of Jito bundle protection
- **🌐 WebSocket Support:** Real-time data streaming to dashboard
- **📱 Professional UI:** Clean, white design optimized for hedge fund operations

---

## 🏗️ Architecture

### **Enhanced API Server** (`phase_4_deployment/dashboard/api_server.py`)
- **FastAPI-based** with WebSocket support
- **Live Trading Integration** via log parsing and RPC calls
- **Real-time Metrics** updated every 30 seconds
- **Comprehensive Endpoints** for all dashboard data needs

### **React Dashboard** (`react-dashboard/`)
- **Material-UI** professional design
- **React Query** for efficient data fetching
- **30-second refresh** aligned with live trading system
- **Responsive Design** for desktop and mobile

---

## 🚀 Quick Start

### 1. **Start Enhanced Dashboard System**
```bash
# Start both API server and React dashboard
python3 scripts/start_enhanced_dashboard.py
```

### 2. **Access Dashboard**
- **Dashboard:** http://localhost:3000
- **API:** http://localhost:8081
- **API Docs:** http://localhost:8081/docs

### 3. **Test API Server**
```bash
# Test API endpoints independently
python3 scripts/test_enhanced_api.py
```

---

## 📊 API Endpoints

### **Core Endpoints**
- `GET /` - API information
- `GET /health` - System health with live trading status
- `GET /metrics` - Complete live trading metrics
- `GET /live-status` - Real-time trading status summary

### **Live Trading Data**
- `GET /wallet-info` - Real-time wallet balance and SOL price
- `GET /trading-session` - Current trading session data
- `GET /component/{component}` - Individual component status

### **WebSocket**
- `WS /ws` - Real-time metrics streaming (30-second updates)

---

## 🔧 Configuration

### **Environment Variables**
```bash
# Required for live trading integration
WALLET_ADDRESS=your_wallet_address
WALLET_PRIVATE_KEY=your_private_key
HELIUS_API_KEY=your_helius_key
QUICKNODE_RPC_URL=your_quicknode_url

# Optional
JITO_RPC_URL=https://slc.mainnet.block-engine.jito.wtf/api/v1
JUPITER_QUOTE_ENDPOINT=https://quote-api.jup.ag/v6/quote
JUPITER_SWAP_ENDPOINT=https://quote-api.jup.ag/v6/swap-instructions
```

### **API Server Configuration**
```python
# Default settings
API_HOST = "0.0.0.0"
API_PORT = 8081
UPDATE_INTERVAL = 30  # seconds
```

---

## 📈 Live Data Integration

### **Real-time Metrics**
- **Wallet Balance:** Direct blockchain queries via Helius RPC
- **SOL Price:** Live pricing from Jupiter DEX API
- **Trading Activity:** Parsed from live trading system logs
- **System Health:** Component status monitoring

### **Data Flow**
1. **Live Trading System** → Logs trading activity
2. **Enhanced API Server** → Parses logs + fetches live data
3. **Background Task** → Updates metrics every 30 seconds
4. **WebSocket/HTTP** → Streams data to React dashboard
5. **Dashboard** → Displays real-time professional interface

---

## 🛡️ Security Features

- **Environment Variables** for sensitive data
- **CORS Protection** with configurable origins
- **Error Handling** with fallback data
- **Connection Monitoring** with automatic reconnection

---

## 📱 Dashboard Features

### **Key Performance Metrics**
- Assets Under Management (SOL + USD)
- Net Performance (P&L tracking)
- Strategy Success Rate
- Real-time Market Price

### **Trading Overview**
- Live trading status indicator
- MEV protection status
- Recent trade history
- Performance charts

### **System Monitoring**
- Component health status
- Network connectivity
- RPC endpoint status
- Risk management status

---

## 🔄 30-Second Update Cycle

### **Synchronized Updates**
- **API Server:** Background task updates metrics every 30 seconds
- **React Dashboard:** Queries refresh every 30 seconds
- **WebSocket:** Real-time streaming every 30 seconds
- **Live Trading System:** Generates new data every 30 seconds

### **Data Freshness**
- **Wallet Balance:** Real-time blockchain queries
- **SOL Price:** Live Jupiter API data
- **Trading Metrics:** Parsed from current session logs
- **System Health:** Real-time component monitoring

---

## 🎯 Professional Design

### **Williams Capital Management Branding**
- **Owner:** Winsor Williams II
- **Clean White Theme** with blue accents
- **Professional Typography** and spacing
- **Hedge Fund Optimized** interface design

### **Responsive Layout**
- **Desktop First** design approach
- **Mobile Compatible** for monitoring on-the-go
- **High-DPI Support** for professional displays

---

## 🚨 Troubleshooting

### **Common Issues**

1. **API Server Won't Start**
   ```bash
   # Check environment variables
   python3 -c "import os; print(os.getenv('WALLET_ADDRESS'))"
   
   # Check port availability
   lsof -i :8081
   ```

2. **Dashboard Shows No Data**
   ```bash
   # Test API connectivity
   curl http://localhost:8081/health
   
   # Check API logs
   tail -f logs/enhanced_api_server.log
   ```

3. **Live Data Not Updating**
   ```bash
   # Check trading system logs
   ls -la logs/debug_live_trading_*.log
   
   # Verify wallet connectivity
   curl http://localhost:8081/wallet-info
   ```

---

## 📞 Support

For technical support or customization requests for the Williams Capital Management trading system, please refer to the main project documentation.

**🏢 Williams Capital Management**  
**👤 Winsor Williams II**  
**🛡️ MEV-Protected • Live Trading • Professional Dashboard**
