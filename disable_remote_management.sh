#!/bin/bash

# Script to disable Apple Remote Management/ARD
# WARNING: This will disable remote management capabilities on your Mac

echo "🔧 Disabling Apple Remote Management/ARD..."
echo "⚠️  WARNING: This will disable remote management capabilities"
echo ""

# Unload the ARD Agent daemon
echo "1. Unloading ARD Agent daemon..."
sudo launchctl unload -w /System/Library/LaunchDaemons/com.apple.RemoteManagement.ARDAgent.plist

# Deactivate and configure ARD access
echo "2. Deactivating ARD access..."
sudo /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off

# Remove ARD Agent application (be careful with this one)
echo "3. Removing ARD Agent application..."
sudo rm -rf /System/Library/CoreServices/RemoteManagement/ARDAgent.app

# Remove preference files
echo "4. Removing preference files..."
sudo rm -rf /Library/Preferences/com.apple.RemoteManagement.plist
sudo rm -rf /Library/Preferences/com.apple.RemoteDesktop.plist

# Remove RemoteManagement database
echo "5. Removing RemoteManagement database..."
sudo rm -rf /var/db/RemoteManagement

echo ""
echo "✅ Apple Remote Management/ARD has been disabled"
echo "⚠️  Note: Some files may be protected by System Integrity Protection (SIP)"
echo "💡 You may need to restart your Mac for all changes to take effect"
