#!/bin/bash

# Error out if anything fails.
set -e

# Parse command line arguments
USERNAME=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --user)
      USERNAME="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 --user <username>"
      exit 1
      ;;
  esac
done

# Check if username was provided
if [ -z "$USERNAME" ]; then
  USERNAME="pi"
fi

if [ ! -d /home/$USERNAME ]; then
    echo "User: $USERNAME home directory not found. Try: ./install.sh --user <yourusername>"
    exit 1
fi

# Make sure script is run as root.
if [ "$(id -u)" != "0" ]; then
  echo "Must be run as root with sudo! Try: sudo ./install.sh"
  exit 1
fi


echo "Installing linux dependencies..."
echo "=========================="
apt update && apt -y install python3 python3-pip

echo "Making virtualenv ..."
echo "=========================="
python -m venv /home/$USERNAME/venvs/pi_video_looper2_venv --system-site-packages
chown -R $USERNAME:$USERNAME /home/$USERNAME/venvs/pi_video_looper2_venv
source /home/$USERNAME/venvs/pi_video_looper2_venv/bin/activate

echo "Installing Adafruit_Blinka..."
echo "=========================="

pip install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sed -i '/shell.prompt_reboot()/d' raspi-blinka.py
/home/$USERNAME/venvs/pi_video_looper2_venv/bin/python raspi-blinka.py
rm raspi-blinka.py
rm -rf -- lg/

echo "Installing pi_video_looper2 program..."
echo "=================================="

# change the directory to the script location
cd "$(dirname "$0")"

pip install ./

# Create the shared video upload directory
echo "Creating video upload directory..."
mkdir -p /home/$USERNAME/Videos
chown $USERNAME:$USERNAME /home/$USERNAME/Videos

# Copy the ini template file
cp ./assets/video_looper.ini.template ./assets/video_looper.ini

# Replace {USERNAME} with the actual username
sed -i "s/{USERNAME}/$USERNAME/g" ./assets/video_looper.ini

# Copy the updated ini file to /boot/
cp ./assets/video_looper.ini /boot/video_looper.ini

echo "Configuring video_looper to run on start..."
echo "==========================================="

# Copy the ini template file
cp ./assets/video_looper.service.template ./assets/video_looper.service

# Replace {USERNAME} with the actual username
sed -i "s/{USERNAME}/$USERNAME/g" ./assets/video_looper.service

cp ./assets/video_looper.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable video_looper
systemctl start video_looper

echo "Configuring video_web (web management server) to run on start..."
echo "================================================================="

# Copy the web server service template
cp ./assets/video_web.service.template ./assets/video_web.service

# Replace {USERNAME} with the actual username
sed -i "s/{USERNAME}/$USERNAME/g" ./assets/video_web.service

cp ./assets/video_web.service /etc/systemd/system/

systemctl daemon-reload
systemctl enable video_web
systemctl start video_web

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo "The web interface is accessible at:"
PI_IP=$(hostname -I | awk '{print $1}')
PI_HOST=$(hostname)
echo "  http://${PI_IP}:5000"
echo "  http://${PI_HOST}.local:5000"
echo ""
echo "Upload videos from any device on the same Wi-Fi network."
echo "========================================="
