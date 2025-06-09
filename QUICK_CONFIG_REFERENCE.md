# Quick Configuration Reference
## RWA Trading System - Live Trading Setup

### 🚀 Quick Start Commands

```bash
# 1. Interactive setup
python3 scripts/setup_live_config.py

# 2. Validate configuration
python3 scripts/validate_live_config.py

# 3. Test endpoints
python3 scripts/test_live_endpoints.py

# 4. Start dashboard
python3 scripts/launch_live_dashboard.py

# 5. Start live trading
python3 scripts/unified_live_trading.py
```

### 📝 Required Environment Variables

Copy these to your `.env` file and fill in your values:

```env
# QuickNode (Primary RPC)
QUICKNODE_RPC_URL=https://your-endpoint.solana-mainnet.quiknode.pro/your-api-key/
QUICKNODE_API_KEY=your_quicknode_api_key_here

# Helius (Fallback RPC)
HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=your_helius_api_key
HELIUS_API_KEY=your_helius_api_key_here

# Wallet
WALLET_ADDRESS=your_wallet_public_key_here
WALLET_PRIVATE_KEY=your_wallet_private_key_here

# Jito (Auto-configured)
JITO_RPC_URL=https://mainnet.block-engine.jito.wtf/api/v1
```

### 🔗 Where to Get API Keys

| Service | URL | Purpose |
|---------|-----|---------|
| QuickNode | https://www.quicknode.com/ | Primary RPC endpoint |
| Helius | https://www.helius.dev/ | Enhanced Solana APIs |
| Birdeye | https://birdeye.so/ | Market data (optional) |
| CoinGecko | https://www.coingecko.com/en/api | Price feeds (optional) |

### ⚙️ Key Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys and secrets |
| `config.yaml` | Main system configuration |
| `config/live_production.yaml` | Live trading parameters |
| `config/whale_wallets.json` | Known whale addresses |

### 🛡️ Safety Settings

```yaml
# In config/live_production.yaml
risk_management:
  max_daily_loss: 0.05          # 5% max daily loss
  max_portfolio_exposure: 0.5   # 50% max exposure
  max_risk_per_trade: 0.02      # 2% risk per trade

trading:
  min_trade_size_usd: 50        # $50 minimum
  target_trade_size_usd: 200    # $200 target
  max_trades_per_day: 20        # 20 trades max
```

### 📊 Monitoring URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Dashboard | http://localhost:8501 | Live trading dashboard |
| API Server | http://localhost:8000 | System API (if running) |

### 🚨 Emergency Commands

```bash
# Stop all trading
pkill -f "unified_live_trading"

# Emergency stop script
python3 scripts/emergency_stop.py

# Check system status
python3 scripts/system_status_check.py
```

### ✅ Pre-Trading Checklist

- [ ] `.env` file configured with real API keys
- [ ] Validation script passes: `python3 scripts/validate_live_config.py`
- [ ] Endpoint tests pass: `python3 scripts/test_live_endpoints.py`
- [ ] Wallet has sufficient SOL balance (>1 SOL recommended)
- [ ] Dashboard is accessible at http://localhost:8501
- [ ] Risk parameters are appropriate for your capital
- [ ] Emergency stop procedures are understood

### 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Module not found" | `pip3 install -r requirements.txt` |
| "API key invalid" | Check API keys in `.env` file |
| "Wallet not found" | Verify `WALLET_ADDRESS` in `.env` |
| "RPC connection failed" | Check `QUICKNODE_RPC_URL` |
| "Insufficient balance" | Add SOL to trading wallet |

### 📱 Optional: Telegram Alerts

```env
# Add to .env for trading alerts
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

Setup:
1. Message @BotFather on Telegram → Create bot → Get token
2. Message @userinfobot on Telegram → Get your chat ID

### 🎯 System Architecture

```
Market Data → Signal Generation → Jupiter Quote → QuickNode Bundle → Jito Execution
     ↓              ↓                  ↓              ↓              ↓
  Birdeye/      Strategy         DEX Routing    Atomic Bundle    MEV Protection
  Helius        Engine           & Pricing      Execution        & Priority
```

### 💡 Pro Tips

1. **Start Small**: Begin with minimum trade sizes
2. **Monitor Closely**: Watch the dashboard during first trades
3. **Test First**: Use the validation and test scripts
4. **Keep Reserves**: Don't use 100% of wallet balance
5. **Stay Updated**: Monitor logs and system health

### ⚠️ Final Warning

**This system trades real money on Solana mainnet. Only use funds you can afford to lose. Cryptocurrency trading involves significant risk.**
