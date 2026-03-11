#!/bin/bash

set -e

if [ "$(id -u)" != "0" ]; then
  echo "Must be run as root. Try: sudo ./setup_hotspot.sh"
  exit 1
fi

SSID="VideoLooper"
PASSWORD="looper123"
HOSTNAME="videolooper"
CON_NAME="VideoLooperHotspot"

echo "=== Setting hostname to '$HOSTNAME' ==="
hostnamectl set-hostname "$HOSTNAME"
# Also update /etc/hosts so local resolution works
sed -i "s/127\.0\.1\.1.*/127.0.1.1\t$HOSTNAME/" /etc/hosts

echo "=== Installing avahi-daemon (mDNS) ==="
apt-get install -y avahi-daemon

echo "=== Creating Wi-Fi hotspot '$SSID' ==="
# Remove existing connection with same name if any
nmcli connection delete "$CON_NAME" 2>/dev/null || true

nmcli device wifi hotspot \
  ifname wlan0 \
  ssid "$SSID" \
  password "$PASSWORD" \
  con-name "$CON_NAME"

# Auto-connect at boot with high priority
nmcli connection modify "$CON_NAME" \
  connection.autoconnect yes \
  connection.autoconnect-priority 10

echo "=== Enabling services ==="
systemctl enable avahi-daemon
systemctl restart avahi-daemon

echo ""
echo "========================================="
echo "Hotspot configured!"
echo "  SSID    : $SSID"
echo "  Password: $PASSWORD"
echo "  URL     : http://$HOSTNAME.local:5000"
echo "========================================="
echo "Reboot for changes to take effect:"
echo "  sudo reboot"
