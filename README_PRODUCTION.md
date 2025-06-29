# Production Deployment Guide for Exotel Bot

This guide provides instructions for deploying the Exotel Bot on a Google Cloud VM for production use.

## System Requirements

- Google Cloud VM with Ubuntu 20.04 LTS or newer
- At least 4GB RAM (8GB recommended)
- At least 20GB disk space
- Python 3.8 or newer
- Supabase project for data storage

## Setup Instructions

### 1. Prepare the VM

1. Create a Google Cloud VM instance:
   ```
   gcloud compute instances create exotel-bot \
     --machine-type=e2-standard-2 \
     --zone=asia-south1-a \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --boot-disk-size=20GB \
     --tags=http-server,https-server
   ```

2. SSH into the VM:
   ```
   gcloud compute ssh exotel-bot
   ```

3. Clone the repository:
   ```
   git clone https://github.com/your-org/abc-angamaly.git
   cd abc-angamaly
   ```

### 2. Configure Environment

1. Make the setup script executable:
   ```
   chmod +x setup_gcp.sh
   ```

2. Run the setup script:
   ```
   sudo ./setup_gcp.sh
   ```

3. Configure your `.env` file:
   ```
   sudo nano /home/exotelbot/abc-angamaly/.env
   ```
   
   Update the following values:
   ```
   WEBHOOK_URL="https://your-domain.com"
   SUPABASE_URL="your-supabase-project-url"
   SUPABASE_KEY="your-supabase-service-role-key"
   SUPABASE_ANON_KEY="your-supabase-anon-key"
   GEMINI_API_KEY="your-api-key"
   ```

### 3. Configure Domain and SSL

1. Update the Nginx configuration with your domain:
   ```
   sudo nano /etc/nginx/sites-available/exotelbot
   ```
   
   Replace `exotel-bot.example.com` with your actual domain.

2. Set up SSL with Let's Encrypt:
   ```
   sudo certbot --nginx -d your-domain.com --non-interactive --agree-tos --email your-email@example.com
   ```

### 4. Verify Deployment

1. Check if the service is running:
   ```
   sudo systemctl status exotel-bot
   ```

2. Check the logs:
   ```
   tail -f /home/exotelbot/abc-angamaly/logs/app.log
   ```

3. Test the Supabase connection:
   ```
   cd /home/exotelbot/abc-angamaly
   source venv/bin/activate
   python -c "from supabase_client import check_supabase; print('Supabase connected:', check_supabase())"
   ```

## Monitoring and Maintenance

### Monitoring

The setup includes a monitoring script that runs every 5 minutes via cron. It checks:
- Service status
- Memory usage
- Disk usage

Alerts are sent to a configured webhook (Slack by default).

### Log Management

Logs are rotated daily and kept for 14 days. You can find logs in:
- Application logs: `/home/exotelbot/abc-angamaly/logs/app.log`
- Supervisor logs: `/home/exotelbot/abc-angamaly/logs/supervisor_*.log`
- Monitoring logs: `/home/exotelbot/abc-angamaly/logs/monitor.log`

### Common Operations

1. Restart the service:
   ```
   sudo systemctl restart exotel-bot
   ```
   
   Or if using supervisor:
   ```
   sudo supervisorctl restart exotelbot
   ```

2. View real-time logs:
   ```
   sudo journalctl -fu exotel-bot
   ```

3. Update the application:
   ```
   cd /home/exotelbot/abc-angamaly
   sudo -u exotelbot git pull
   sudo systemctl restart exotel-bot
   ```

## Performance Tuning

### Memory Optimization

The application includes automatic memory monitoring and garbage collection. If you experience memory issues:

1. Adjust the memory limit in the systemd service:
   ```
   sudo nano /etc/systemd/system/exotel-bot.service
   ```
   
   Update the `MemoryLimit` value and reload:
   ```
   sudo systemctl daemon-reload
   sudo systemctl restart exotel-bot
   ```

2. Adjust cache TTLs in `call_flow.py` for better memory management.

### Connection Handling

The WebSocket server is configured with:
- 10MB max message size for audio data
- 30-second ping interval
- 10-second ping timeout
- 10-second close timeout

Adjust these values in `main_enhanced.py` if needed.

## Troubleshooting

### Service Issues

1. Check for errors:
   ```
   sudo journalctl -fu exotel-bot
   ```

2. Verify Python dependencies:
   ```
   /home/exotelbot/abc-angamaly/venv/bin/pip list
   ```

3. Check Supabase connection:
   ```
   cd /home/exotelbot/abc-angamaly
   source venv/bin/activate
   python -c "from supabase_client import check_supabase; print(check_supabase())"
   ```

### WebSocket Connection Issues

1. Check if the port is open:
   ```
   sudo ufw status
   ```

2. Verify Nginx configuration:
   ```
   sudo nginx -t
   ```

3. Test local connection:
   ```
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Host: localhost" -H "Origin: http://localhost" \
     http://localhost:8080
   ```

## Security Considerations

1. The setup includes basic security measures:
   - Dedicated user account
   - Firewall configuration
   - SSL encryption
   - Process isolation

2. Additional recommended measures:
   - Set up Google Cloud IAM roles properly
   - Enable Google Cloud Armor for DDoS protection
   - Implement IP allowlisting if possible
   - Regularly update dependencies

## Backup Strategy

1. Set up automated backups for:
   - Customer data: `/home/exotelbot/abc-angamaly/data/customers`
   - Call sessions: `/home/exotelbot/abc-angamaly/data/call_sessions`
   - Supabase data: Use Supabase's built-in backup features

2. Example backup script:
   ```bash
   #!/bin/bash
   BACKUP_DIR="/backups/exotelbot/$(date +%Y%m%d)"
   mkdir -p $BACKUP_DIR
   cp -r /home/exotelbot/abc-angamaly/data $BACKUP_DIR/
   ```

## Scaling Considerations

For higher load scenarios:
1. Increase VM resources (CPU/RAM)
2. Set up multiple instances behind a load balancer
3. Use Supabase's built-in scaling features
4. Implement a distributed task queue for processing 