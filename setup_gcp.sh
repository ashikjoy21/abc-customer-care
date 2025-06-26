#!/bin/bash
# Setup script for Exotel Bot on Google Cloud VM
set -e

# Update and install system dependencies
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv redis-server supervisor nginx certbot python3-certbot-nginx

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

# Configure Redis
echo "Configuring Redis..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

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
cat > /tmp/exotelbot_nginx << 'EOL'
server {
    listen 80;
    server_name exotel-bot.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }
}
EOL

sudo mv /tmp/exotelbot_nginx /etc/nginx/sites-available/exotelbot
sudo ln -sf /etc/nginx/sites-available/exotelbot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Set up SSL with Let's Encrypt (uncomment and modify when domain is ready)
# echo "Setting up SSL with Let's Encrypt..."
# sudo certbot --nginx -d exotel-bot.example.com --non-interactive --agree-tos --email admin@example.com

# Set up firewall
echo "Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable

# Set up log rotation
echo "Setting up log rotation..."
cat > /tmp/exotelbot_logrotate << 'EOL'
/home/exotelbot/abc-angamaly/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 exotelbot exotelbot
    sharedscripts
    postrotate
        supervisorctl restart exotelbot >/dev/null 2>&1 || true
    endscript
}
EOL

sudo mv /tmp/exotelbot_logrotate /etc/logrotate.d/exotelbot

# Create a monitoring script
echo "Creating monitoring script..."
cat > $APP_DIR/monitor.sh << 'EOL'
#!/bin/bash
# Simple monitoring script

LOG_FILE="/home/exotelbot/abc-angamaly/logs/monitor.log"
WEBHOOK_URL="https://hooks.slack.com/services/your/webhook/url"

check_service() {
    if ! pgrep -f "main_enhanced.py" > /dev/null; then
        echo "$(date): Service is down! Attempting to restart..." >> $LOG_FILE
        supervisorctl restart exotelbot
        curl -X POST -H 'Content-type: application/json' --data '{"text":"⚠️ Exotel Bot service is down and was restarted"}' $WEBHOOK_URL
    else
        echo "$(date): Service is running" >> $LOG_FILE
    fi
}

check_memory() {
    MEM_USAGE=$(ps aux | grep "main_enhanced.py" | grep -v grep | awk '{print $4}')
    if [[ $(echo "$MEM_USAGE > 80.0" | bc) -eq 1 ]]; then
        echo "$(date): High memory usage: $MEM_USAGE%" >> $LOG_FILE
        curl -X POST -H 'Content-type: application/json' --data '{"text":"⚠️ Exotel Bot high memory usage: '"$MEM_USAGE"'%"}' $WEBHOOK_URL
    fi
}

check_disk() {
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $DISK_USAGE -gt 85 ]]; then
        echo "$(date): High disk usage: $DISK_USAGE%" >> $LOG_FILE
        curl -X POST -H 'Content-type: application/json' --data '{"text":"⚠️ Exotel Bot server high disk usage: '"$DISK_USAGE"'%"}' $WEBHOOK_URL
    fi
}

check_service
check_memory
check_disk
EOL

sudo chmod +x $APP_DIR/monitor.sh
sudo chown exotelbot:exotelbot $APP_DIR/monitor.sh

# Add cron job for monitoring
echo "Setting up cron job for monitoring..."
(crontab -u exotelbot -l 2>/dev/null || echo "") | { cat; echo "*/5 * * * * $APP_DIR/monitor.sh"; } | crontab -u exotelbot -

echo "Setup completed successfully!"
echo "The Exotel Bot is now running at http://localhost:8080"
echo "Configure your domain and SSL when ready." 