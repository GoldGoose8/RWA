#!/bin/bash
# Winsor Williams II - Hedge Fund Dashboard Launcher
# MEV-Protected Trading Dashboard

echo "🏢 Winsor Williams II - Hedge Fund"
echo "🚀 MEV-Protected Trading Dashboard"
echo "🛡️ Jito Block Engine • QuickNode Bundles"
echo ""

# Check if trading system is running
if pgrep -f "unified_live_trading.py" > /dev/null; then
    echo "✅ Live trading system is running"
else
    echo "⚠️ Live trading system not detected"
    echo "💡 Start it with: python3 scripts/unified_live_trading.py"
fi

echo ""
echo "📊 Starting dashboard at http://localhost:8501"
echo "🔄 Dashboard updates every 30 seconds"
echo "👤 Owner: Winsor Williams II"
echo ""

# Start the dashboard
python3 scripts/start_winsor_dashboard.py
