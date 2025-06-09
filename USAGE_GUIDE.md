# 🎯 SYNERGY7 SYSTEM - 3 ENTRY POINTS USAGE GUIDE

## **SYSTEM CONSOLIDATED TO 3 SINGLE ENTRY POINTS**

### **1. 🔴 LIVE TRADING**
```bash
# Live trading with real money
cd /Users/Quantzavant/HedgeFund
DRY_RUN=false TRADING_ENABLED=true python3 scripts/unified_live_trading.py --duration 60
```

### **2. 📊 BACKTESTING**
```bash
# Historical backtesting
cd /Users/Quantzavant/HedgeFund
python3 phase_4_deployment/unified_runner.py --mode backtest
```

### **3. 📝 PAPER TRADING**
```bash
# Paper trading simulation
cd /Users/Quantzavant/HedgeFund
python3 phase_4_deployment/unified_runner.py --mode paper
```

## **ESSENTIAL SUPPORT COMMANDS**

### **Dashboard**
```bash
streamlit run phase_4_deployment/dashboard/streamlit_dashboard.py
```

### **System Health**
```bash
python3 phase_4_deployment/monitoring/health_check_server.py
```

### **Trade Analysis**
```bash
python3 scripts/rich_trade_analyzer.py
```

### **System Tests**
```bash
python3 scripts/comprehensive_system_test.py
```

## **ALL OTHER ENTRY POINTS REMOVED**
- No more confusion with multiple entry points
- No more redundant scripts
- Clean, focused architecture
- Single source of truth for each function
