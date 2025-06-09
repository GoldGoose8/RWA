# Live Trading Setup Guide
## RWA Trading System Configuration

This guide will help you configure the RWA Trading System for live trading on Solana mainnet.

## 🚨 Prerequisites

Before starting, ensure you have:
- A funded Solana wallet for trading
- QuickNode account with Solana mainnet endpoint
- Helius account for enhanced Solana APIs
- Basic understanding of cryptocurrency trading risks

## 📋 Step-by-Step Configuration

### Step 1: Run the Interactive Setup Assistant

```bash
python3 scripts/setup_live_config.py
```

This interactive script will guide you through:
- QuickNode RPC configuration
- Helius API setup
- Wallet configuration
- Optional Telegram alerts
- Optional market data APIs

### Step 2: Manual Configuration (Alternative)

If you prefer manual configuration, edit the `.env` file directly:

#### Required API Keys and Endpoints

1. **QuickNode Configuration**
   ```env
   QUICKNODE_RPC_URL=https://your-endpoint.solana-mainnet.quiknode.pro/your-api-key/
   QUICKNODE_API_KEY=your_quicknode_api_key_here
   ```
   - Sign up at: https://www.quicknode.com/
   - Create a Solana Mainnet endpoint
   - Copy the RPC URL and API key

2. **Helius Configuration**
   ```env
   HELIUS_RPC_URL=https://mainnet.helius-rpc.com/?api-key=your_helius_api_key
   HELIUS_API_KEY=your_helius_api_key_here
   ```
   - Sign up at: https://www.helius.dev/
   - Create an API key
   - The RPC URL includes your API key

3. **Wallet Configuration**
   ```env
   WALLET_ADDRESS=your_wallet_public_key_here
   WALLET_PRIVATE_KEY=your_wallet_private_key_here
   KEYPAIR_PATH=keys/trading_wallet.json
   ```
   - Use your Solana trading wallet
   - ⚠️ **SECURITY**: Keep private key secure!

### Step 3: Validate Configuration

Run the validation script to check your setup:

```bash
python3 scripts/validate_live_config.py
```

This will verify:
- ✅ All required environment variables are set
- ✅ API endpoints are reachable
- ✅ Wallet configuration is valid
- ✅ Network connectivity is working

### Step 4: Test Endpoints

Test all endpoints and transaction capabilities:

```bash
python3 scripts/test_live_endpoints.py
```

This will test:
- QuickNode RPC performance
- Helius API connectivity
- Jito bundle endpoint
- Jupiter DEX API
- Wallet balance retrieval

## 🔧 Configuration Details

### RPC Endpoint Priority

The system uses a multi-tier RPC approach:

1. **Primary**: QuickNode (High performance, low latency)
2. **Fallback**: Helius (Enhanced APIs, reliable)
3. **Bundle Execution**: Jito (MEV protection)

### Transaction Execution Flow

```
Signal Generated → Jupiter Quote → QuickNode Bundle → Jito Submission
```

### Risk Management Settings

Key safety parameters in `config/live_production.yaml`:

```yaml
risk_management:
  max_daily_loss: 0.05          # 5% max daily loss
  max_portfolio_exposure: 0.5   # 50% max exposure
  max_risk_per_trade: 0.02      # 2% risk per trade
  
trading:
  min_trade_size_usd: 50        # $50 minimum trade
  target_trade_size_usd: 200    # $200 target trade
  max_trades_per_day: 20        # 20 trades max per day
```

## 🛡️ Security Best Practices

### Environment Variables
- Never commit `.env` file to version control
- Use secure key management in production
- Regularly rotate API keys

### Wallet Security
- Use a dedicated trading wallet
- Keep only necessary funds in trading wallet
- Monitor wallet activity regularly

### Network Security
- Use VPN for additional security
- Monitor for unusual API activity
- Set up alerts for large transactions

## 📊 Monitoring and Alerts

### Telegram Alerts (Optional)

1. Create a Telegram bot:
   - Message @BotFather on Telegram
   - Create new bot with `/newbot`
   - Save the bot token

2. Get your chat ID:
   - Message @userinfobot on Telegram
   - Save your chat ID

3. Configure in `.env`:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   TELEGRAM_CHAT_ID=your_telegram_chat_id_here
   ```

### Dashboard Monitoring

The Streamlit dashboard provides real-time monitoring:
- Live trading metrics
- Transaction history
- System health status
- Performance analytics

Access at: http://localhost:8501

## 🚀 Starting Live Trading

### Final Checklist

Before starting live trading, ensure:

- [ ] All validation tests pass
- [ ] Endpoint tests are successful
- [ ] Wallet has sufficient SOL balance
- [ ] Risk parameters are configured
- [ ] Monitoring is set up
- [ ] Emergency stop procedures are understood

### Launch Commands

1. **Start the dashboard** (if not already running):
   ```bash
   python3 scripts/launch_live_dashboard.py
   ```

2. **Start live trading**:
   ```bash
   python3 scripts/unified_live_trading.py
   ```

## ⚠️ Important Warnings

### Financial Risks
- Cryptocurrency trading involves significant risk
- Only trade with funds you can afford to lose
- Past performance does not guarantee future results
- Market conditions can change rapidly

### Technical Risks
- Network connectivity issues can affect trading
- API rate limits may impact performance
- Smart contract risks exist with DEX interactions
- MEV (Maximum Extractable Value) can affect trades

### Operational Risks
- Monitor system continuously during trading
- Have emergency stop procedures ready
- Keep backup RPC endpoints configured
- Maintain adequate wallet balances

## 🆘 Emergency Procedures

### Emergency Stop
```bash
# Kill all trading processes
pkill -f "unified_live_trading"

# Or use the emergency stop script
python3 scripts/emergency_stop.py
```

### Position Flattening
The system includes automatic position flattening:
- End of session flattening
- Risk threshold flattening
- Emergency error flattening

### Support and Troubleshooting

1. **Check logs**: `logs/live_production.log`
2. **Validate config**: `python3 scripts/validate_live_config.py`
3. **Test endpoints**: `python3 scripts/test_live_endpoints.py`
4. **Monitor dashboard**: http://localhost:8501

## 📞 Getting Help

If you encounter issues:
1. Check the validation and test scripts
2. Review the logs for error messages
3. Ensure all API keys are valid and active
4. Verify wallet has sufficient balance
5. Check network connectivity

Remember: **Never trade with more than you can afford to lose!**
