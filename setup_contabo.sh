#!/bin/bash

echo "🛠️ Setting up your VPS..."

apt update && apt upgrade -y
apt install -y wget unzip nano curl software-properties-common apt-transport-https ca-certificates gnupg python3 python3-pip python3-venv xfce4 xfce4-goodies tightvncserver

# Install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb || apt --fix-broken install -y

# ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROMEDRIVER_URL=$(curl -sS https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json | grep -A 20 "$CHROME_VERSION" | grep "chromedriver-linux64.zip" | head -1 | grep -o 'https[^"]*')
wget -O chromedriver.zip "$CHROMEDRIVER_URL"
unzip chromedriver.zip
mv chromedriver-linux64/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Python packages
pip3 install selenium selenium-wire python-dotenv pyttsx3 webdriver-manager

# VNC setup
vncserver :1
vncserver -kill :1
mkdir -p ~/.vnc
cat > ~/.vnc/xstartup <<EOL
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOL
chmod +x ~/.vnc/xstartup

echo "✅ VPS setup complete! VNC running on port 5901"

