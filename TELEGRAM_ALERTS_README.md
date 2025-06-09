# Telegram Alerts System - Williams Capital Management

## 🚀 Professional Trading Alerts for Winsor Williams II

Professional Telegram alerts system designed for Williams Capital Management hedge fund operations. Get real-time notifications for all trading activities, system status, and performance metrics.

---

## ✨ Features

- **🔧 Interactive Setup** - Automated bot token and chat ID configuration
- **💰 Trade Alerts** - Real-time trade execution notifications
- **📊 Performance Updates** - Session summaries and milestone alerts
- **🛡️ System Monitoring** - MEV protection and system status alerts
- **⚠️ Risk Management** - Automated risk threshold notifications
- **💼 Balance Tracking** - Wallet balance and P&L updates
- **🎯 Professional Formatting** - Clean, branded message templates

---

## 🚀 Quick Start

### 1. **Initial Setup**
```bash
# Run interactive setup (will guide you through bot creation)
python3 scripts/telegram_alerts_setup.py

# Or with specific options
python3 scripts/telegram_alerts_setup.py --setup
```

### 2. **Test Configuration**
```bash
# Test existing configuration
python3 scripts/telegram_alerts_setup.py --test

# Run full integration test
python3 scripts/test_telegram_integration.py
```

### 3. **Integration with Trading System**
```python
from scripts.telegram_trading_alerts import TradingAlerts

alerts = TradingAlerts()

# Send trade execution alert
await alerts.trade_executed("0.1 SOL", "$152.45", "5xG7d...")

# Send system status
await alerts.system_online()

# Send session summary
await alerts.session_summary(25, 88, "+2.5 SOL")
```

---

## 📋 Bot Setup Instructions

### **Creating Your Telegram Bot:**

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather
3. **Send `/newbot`** command
4. **Choose a name** for your bot (e.g., "Williams Capital Alerts")
5. **Choose a username** ending in 'bot' (e.g., "williams_capital_bot")
6. **Copy the bot token** (format: `123456789:ABCdefGHI...`)
7. **Send `/start`** to your new bot

### **Getting Your Chat ID:**

**Option 1 - Personal Chat:**
1. Message `@userinfobot` in Telegram
2. Copy your user ID (positive number)

**Option 2 - Group Chat:**
1. Add your bot to the group
2. Send a message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id": NEGATIVE_NUMBER}`

---

## 📱 Alert Types

### **Trade Execution Alerts**
```python
await alerts.trade_executed("0.1 SOL", "$152.45", "5xG7d...", "BUY", True)
```
- Trade type (BUY/SELL)
- Amount and price
- Transaction hash
- Success/failure status

### **System Status Alerts**
```python
await alerts.system_online()
await alerts.system_offline("Maintenance")
```
- System startup/shutdown
- Component status
- Maintenance notifications

### **Performance Updates**
```python
await alerts.session_summary(25, 88, "+2.5 SOL", 4.5)
```
- Total trades executed
- Win rate percentage
- P&L summary
- Session duration

### **Risk Management Alerts**
```python
await alerts.risk_alert("SLIPPAGE_HIGH", "Exceeded 2% threshold", "MEDIUM")
```
- Risk threshold breaches
- Severity levels (LOW/MEDIUM/HIGH/CRITICAL)
- Detailed descriptions

### **Balance Updates**
```python
await alerts.balance_update("15.45", 2356.78, -0.05)
```
- Current SOL balance
- USD value
- Balance changes

### **MEV Protection Status**
```python
await alerts.mev_protection_alert("ACTIVE", "Jito bundles operational")
```
- Protection status
- Bundle information
- Security updates

---

## 🔧 Configuration

### **Environment Variables**
The setup script automatically adds these to your `.env` file:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### **Manual Configuration**
If you prefer to set up manually:

1. Create a Telegram bot via @BotFather
2. Get your chat ID via @userinfobot
3. Add the credentials to your `.env` file
4. Test with: `python3 scripts/telegram_alerts_setup.py --test`

---

## 📚 Usage Examples

### **Basic Integration**
```python
from scripts.telegram_trading_alerts import TradingAlerts

# Initialize alerts
alerts = TradingAlerts()

# Check if configured
if alerts.enabled:
    await alerts.trade_executed("0.1 SOL", "$152.45", "5xG7d...")
```

### **Quick Functions**
```python
from scripts.telegram_trading_alerts import notify_trade, notify_system_status

# Quick trade notification
await notify_trade("0.1 SOL", "$152.45", "5xG7d...", "BUY")

# Quick system status
await notify_system_status(True)  # System online
await notify_system_status(False, "Maintenance")  # System offline
```

### **Live Trading Integration**
```python
# In your trading loop
async def execute_trade(signal):
    try:
        # Execute trade
        result = await trading_engine.execute(signal)
        
        # Send success alert
        await alerts.trade_executed(
            f"{signal.amount} SOL",
            f"${signal.price}",
            result.transaction_hash,
            signal.side
        )
        
    except Exception as e:
        # Send failure alert
        await alerts.risk_alert(
            "TRADE_EXECUTION_FAILED",
            str(e),
            "HIGH"
        )
```

---

## 🎯 Professional Message Format

All alerts follow a consistent professional format:

```
🏢 Williams Capital Management
👤 Winsor Williams II
⏰ 2025-06-08 19:30:15

💰 TRADE EXECUTED

✅ Type: BUY
💎 Amount: 0.1 SOL
💲 Price: $152.45
🔗 TX: 5xG7d8k2m9...

🛡️ MEV-Protected Trading System
```

---

## 🔍 Testing & Troubleshooting

### **Test All Alert Types**
```bash
python3 scripts/test_telegram_integration.py
```

### **Test Specific Configuration**
```bash
python3 scripts/telegram_alerts_setup.py --test
```

### **Common Issues**

1. **"Bot token invalid"**
   - Verify token format: `123456789:ABCdefGHI...`
   - Check for extra spaces or characters

2. **"Chat not found"**
   - Ensure you've sent `/start` to your bot
   - Verify chat ID is correct (positive for personal, negative for groups)

3. **"Alerts not configured"**
   - Run setup: `python3 scripts/telegram_alerts_setup.py`
   - Check `.env` file for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

---

## 🏢 Williams Capital Management Integration

This alerts system is specifically designed for Williams Capital Management hedge fund operations:

- **Professional branding** in all messages
- **Winsor Williams II** attribution
- **Hedge fund appropriate** formatting and terminology
- **MEV protection** status monitoring
- **Real-time trading** notifications
- **Performance tracking** for institutional operations

---

## 📞 Support

For technical support or customization requests for the Williams Capital Management trading system, please refer to the main project documentation.

**🏢 Williams Capital Management**  
**👤 Winsor Williams II**  
**📱 Professional Trading Alerts System**
