#!/bin/bash
# Setup script for Exotel Bot on Google Cloud VM
set -e

# Update and install system dependencies
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv supervisor nginx certbot python3-certbot-nginx

# Create user if it doesn't exist
if ! id -u exotelbot &>/dev/null; then
    echo "Creating exotelbot user..."
    sudo useradd -m -s /bin/bash exotelbot
fi

# Set up application directory
APP_DIR="/home/exotelbot/abc-angamaly"
if [ ! -d "$APP_DIR" ]; then
    echo "Creating application directory..."
    sudo mkdir -p $APP_DIR
    sudo chown exotelbot:exotelbot $APP_DIR
fi

# Copy application files
echo "Copying application files..."
sudo cp -r ./* $APP_DIR/
sudo chown -R exotelbot:exotelbot $APP_DIR

# Create required directories
sudo -u exotelbot mkdir -p $APP_DIR/logs
sudo -u exotelbot mkdir -p $APP_DIR/data/call_sessions
sudo -u exotelbot mkdir -p $APP_DIR/data/customers
sudo -u exotelbot mkdir -p $APP_DIR/data/knowledge_base

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
sudo -u exotelbot python3 -m venv $APP_DIR/venv
sudo -u exotelbot $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u exotelbot $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Set up supervisor
echo "Setting up supervisor..."
sudo cp $APP_DIR/supervisor.conf /etc/supervisor/conf.d/exotelbot.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start exotelbot

# Set up systemd service (alternative to supervisor)
echo "Setting up systemd service..."
sudo cp $APP_DIR/exotel-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable exotel-bot.service
sudo systemctl start exotel-bot.service

# Set up Nginx as reverse proxy
echo "Setting up Nginx..."
sudo tee /etc/nginx/sites-available/exotelbot > /dev/null <<EOF
server {
    listen 80;
    server_name exotel-bot.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/exotelbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo "Setup completed successfully!"
echo "Please configure your .env file with Supabase credentials and other settings."
echo "Then restart the service: sudo systemctl restart exotel-bot" 