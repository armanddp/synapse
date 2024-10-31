#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing GoPro Synapse...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt-get update
apt-get install -y python3-venv python3-pip

# Create installation directory
INSTALL_DIR="/opt/gopro-synapse"
mkdir -p $INSTALL_DIR

# Create virtual environment
python3 -m venv $INSTALL_DIR/venv

$INSTALL_DIR/venv/bin/pip install hatch
# Install the package
$INSTALL_DIR/venv/bin/pip install git+https://github.com/armanddp/synapse.git

# Create systemd service
cat > /etc/systemd/system/gopro-livestream.service << EOL
[Unit]
Description=GoPro Livestream Service
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$INSTALL_DIR/venv/bin/gosynapse --config /etc/gopro-synapse/config.ini
WorkingDirectory=$INSTALL_DIR
Restart=always
User=root
Group=root
Environment=PYTHONUNBUFFERED=1
StandardOutput=append:/var/log/gopro-livestream.log
StandardError=append:/var/log/gopro-livestream.log

[Install]
WantedBy=multi-user.target
EOL

# Create config directory and copy template
mkdir -p /etc/gopro-synapse
cp $INSTALL_DIR/venv/lib/python*/site-packages/gosynapse/config/config.template.ini /etc/gopro-synapse/config.ini

# Set up logging
touch /var/log/gopro-livestream.log
chmod 644 /var/log/gopro-livestream.log

# Configure the service
echo -e "\n${YELLOW}Configuring the service...${NC}"
read -p "Enter GoPro SSID: " gopro_ssid
read -p "Enter WiFi SSID: " wifi_ssid
read -p "Enter WiFi password: " wifi_password
read -p "Enter RTMP URL: " rtmp_url

# Update config file
sed -i "s/gopro_ssid=.*/gopro_ssid=$gopro_ssid/" /etc/gopro-synapse/config.ini
sed -i "s/wifi_ssid=.*/wifi_ssid=$wifi_ssid/" /etc/gopro-synapse/config.ini
sed -i "s/wifi_password=.*/wifi_password=$wifi_password/" /etc/gopro-synapse/config.ini
sed -i "s|rtmp_url=.*|rtmp_url=$rtmp_url|" /etc/gopro-synapse/config.ini

# Enable and start service
systemctl daemon-reload
systemctl enable gopro-livestream.service
systemctl start gopro-livestream.service

echo -e "\n${GREEN}Installation complete!${NC}"
echo "Configuration file: /etc/gopro-synapse/config.ini"
echo "Log file: /var/log/gopro-livestream.log"
echo "Check service status with: systemctl status gopro-livestream.service"
