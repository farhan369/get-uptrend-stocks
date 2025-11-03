# Deployment Guide - Single Server Deployment

This guide walks you through deploying both frontend and backend on a single server.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Project Setup](#project-setup)
4. [Database Configuration](#database-configuration)
5. [Environment Variables](#environment-variables)
6. [Backend Configuration](#backend-configuration)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL/HTTPS Setup](#sslhttps-setup)
9. [Process Manager (Systemd)](#process-manager-systemd)
10. [Post-Deployment](#post-deployment)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Ubuntu 20.04 or 22.04 LTS (recommended)
- Root or sudo access
- Domain name pointed to your server's IP address
- At least 2GB RAM and 20GB storage

---

## Step 1: Server Setup

### 1.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Required Packages

```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Nginx
sudo apt install -y nginx

# Install additional tools
sudo apt install -y git curl build-essential libpq-dev
```

### 1.3 Create Deploy User (Optional but Recommended)

```bash
sudo adduser deploy
sudo usermod -aG sudo deploy
su - deploy
```

---

## Step 2: Project Setup

### 2.1 Clone Your Repository

```bash
cd /home/deploy
git clone https://github.com/yourusername/get-uptrend-stocks.git
cd get-uptrend-stocks/nse-trend-stocks
```

Or if uploading files directly:

```bash
cd /home/deploy
mkdir -p nse-stock-platform
cd nse-stock-platform

# Upload your files using scp or rsync
# From your local machine:
# rsync -avz --progress ./nse-trend-stocks/ deploy@your-server-ip:/home/deploy/nse-stock-platform/
```

### 2.2 Create Python Virtual Environment

```bash
cd /home/deploy/nse-stock-platform/backend
python3.11 -m venv venv
source venv/bin/activate
```

### 2.3 Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requiewments.txt
```

---

## Step 3: Database Configuration

### 3.1 Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE stock_trading;
CREATE USER trader WITH ENCRYPTED PASSWORD 'YourStrongPassword123!';
GRANT ALL PRIVILEGES ON DATABASE stock_trading TO trader;
\q
```

### 3.2 Configure PostgreSQL for Remote Access (if needed)

```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Change listen_addresses:
listen_addresses = 'localhost'

# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add this line:
host    stock_trading    trader    127.0.0.1/32    md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## Step 4: Environment Variables

### 4.1 Create .env File

```bash
cd /home/deploy/nse-stock-platform/backend
nano .env
```

Add the following (replace with your actual values):

```env
# Database
DATABASE_URL=postgresql://trader:YourStrongPassword123!@localhost:5432/stock_trading

# Security
SECRET_KEY=your-super-secret-key-generated-with-secrets-module

# Gemini AI (Optional)
GEMINI_API_KEY=your-gemini-api-key

# Google OAuth (Optional)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v2/auth/google/callback
FRONTEND_URL=/static

# Production Settings
ENVIRONMENT=production
```

### 4.2 Generate SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and paste it as SECRET_KEY in .env
```

### 4.3 Secure .env File

```bash
chmod 600 .env
```

---

## Step 5: Backend Configuration

### 5.1 Initialize Database

```bash
source venv/bin/activate
python main.py
# Press Ctrl+C after you see "Database initialized successfully"
```

### 5.2 Test Backend

```bash
python main.py
# Visit http://your-server-ip:8000/docs in your browser
# Press Ctrl+C when done testing
```

---

## Step 6: Nginx Configuration

### 6.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/stock-platform
```

Add the following configuration:

```nginx
# Stock Trading Platform - Nginx Configuration

upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit (for file uploads if needed)
    client_max_body_size 10M;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Root location - serve frontend
    location / {
        root /home/deploy/nse-stock-platform/frontend;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # Static files (CSS, JS, images)
    location /static {
        alias /home/deploy/nse-stock-platform/frontend;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api/ {
        proxy_pass http://fastapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API docs
    location /docs {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /redoc {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 6.2 Enable the Site

```bash
# Test configuration
sudo nginx -t

# Enable site
sudo ln -s /etc/nginx/sites-available/stock-platform /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 7: SSL/HTTPS Setup

### 7.1 Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 7.2 Obtain SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts:
- Enter your email
- Agree to terms
- Choose whether to redirect HTTP to HTTPS (recommended: Yes)

### 7.3 Auto-Renewal Test

```bash
sudo certbot renew --dry-run
```

---

## Step 8: Process Manager (Systemd)

### 8.1 Create Systemd Service

```bash
sudo nano /etc/systemd/system/stock-platform.service
```

Add the following:

```ini
[Unit]
Description=NSE Stock Trading Platform - FastAPI Backend
After=network.target postgresql.service

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/nse-stock-platform/backend
Environment="PATH=/home/deploy/nse-stock-platform/backend/venv/bin"
ExecStart=/home/deploy/nse-stock-platform/backend/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 8.2 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable stock-platform

# Start service
sudo systemctl start stock-platform

# Check status
sudo systemctl status stock-platform
```

### 8.3 View Logs

```bash
# Follow logs in real-time
sudo journalctl -u stock-platform -f

# View recent logs
sudo journalctl -u stock-platform -n 100

# View logs from today
sudo journalctl -u stock-platform --since today
```

---

## Step 9: Post-Deployment

### 9.1 Verify Everything Works

```bash
# Check backend is running
curl http://localhost:8000/api/v2/health

# Check nginx is serving frontend
curl http://localhost/

# Check from outside
curl https://yourdomain.com/api/v2/health
```

### 9.2 Create Admin User (via API)

```bash
curl -X POST "https://yourdomain.com/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "username": "admin",
    "password": "SecurePassword123!",
    "full_name": "Admin User"
  }'
```

### 9.3 Set Up Monitoring (Optional)

```bash
# Install htop for system monitoring
sudo apt install -y htop

# Monitor system resources
htop

# Monitor disk usage
df -h

# Monitor PostgreSQL
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE datname='stock_trading';"
```

### 9.4 Set Up Backups

```bash
# Create backup script
nano ~/backup-database.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="stock_trading_$DATE.sql"

mkdir -p $BACKUP_DIR
pg_dump -U trader -h localhost stock_trading > "$BACKUP_DIR/$FILENAME"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "stock_trading_*.sql" -mtime +7 -delete

echo "Backup completed: $FILENAME"
```

Make it executable and add to cron:

```bash
chmod +x ~/backup-database.sh

# Add to cron (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/deploy/backup-database.sh >> /home/deploy/backup.log 2>&1
```

---

## Step 10: Updating the Application

### 10.1 Update Code

```bash
cd /home/deploy/nse-stock-platform
git pull origin main  # or your branch name
```

### 10.2 Update Dependencies

```bash
cd backend
source venv/bin/activate
pip install -r requiewments.txt --upgrade
```

### 10.3 Restart Service

```bash
sudo systemctl restart stock-platform
```

### 10.4 Zero-Downtime Deployment (Advanced)

For zero-downtime:

```bash
# Run multiple instances with supervisor or use gunicorn with workers
# Example with gunicorn:
pip install gunicorn uvicorn[standard]

# Update systemd service ExecStart:
ExecStart=/home/deploy/nse-stock-platform/backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile - \
    --error-logfile -
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
sudo journalctl -u stock-platform -n 50

# Check if port is in use
sudo lsof -i :8000

# Test manually
cd /home/deploy/nse-stock-platform/backend
source venv/bin/activate
python main.py
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U trader -h localhost -d stock_trading

# Check pg_hba.conf
sudo cat /etc/postgresql/14/main/pg_hba.conf | grep trader
```

### Nginx Issues

```bash
# Check configuration
sudo nginx -t

# Check logs
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R deploy:deploy /home/deploy/nse-stock-platform

# Fix .env permissions
chmod 600 /home/deploy/nse-stock-platform/backend/.env
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate
sudo certbot certificates
```

### High Memory Usage

```bash
# Check memory
free -h

# Restart service
sudo systemctl restart stock-platform

# Consider adding swap
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Security Checklist

- [ ] Strong passwords for all accounts
- [ ] SSH key-based authentication (disable password auth)
- [ ] Firewall configured (ufw)
- [ ] SSL/HTTPS enabled
- [ ] `.env` file secured (chmod 600)
- [ ] Regular backups configured
- [ ] System updates automated
- [ ] Fail2ban installed (optional)
- [ ] Google OAuth credentials secured
- [ ] Database user has limited privileges

---

## Maintenance Commands

```bash
# View application logs
sudo journalctl -u stock-platform -f

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart stock-platform
sudo systemctl restart nginx
sudo systemctl restart postgresql

# Check system resources
htop
df -h
free -h

# Database maintenance
sudo -u postgres psql stock_trading -c "VACUUM ANALYZE;"
```

---

## Performance Optimization

### Enable Caching

Update nginx config to add caching:

```nginx
# Add to http block in /etc/nginx/nginx.conf
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

# In server block, add to API location:
location /api/v2/stocks/screen {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
    add_header X-Cache-Status $upstream_cache_status;
    
    proxy_pass http://fastapi_backend;
    # ... other proxy settings ...
}
```

### Database Optimization

```sql
-- Connect to database
sudo -u postgres psql stock_trading

-- Create indexes
CREATE INDEX idx_trades_user_created ON trades(user_id, created_at DESC);
CREATE INDEX idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX idx_watchlist_user_symbol ON watchlists(user_id, symbol);
```

---

## Support and Monitoring

### Set Up Email Alerts

Install and configure postfix for email alerts:

```bash
sudo apt install -y postfix mailutils

# Configure systemd to send email on service failure
sudo nano /etc/systemd/system/stock-platform.service

# Add under [Service]:
OnFailure=failure-email@%n.service
```

---

## Conclusion

Your application should now be running at `https://yourdomain.com`.

**Key URLs:**
- Frontend: `https://yourdomain.com`
- API Docs: `https://yourdomain.com/docs`
- Health Check: `https://yourdomain.com/api/v2/health`

For questions or issues, check the logs first and refer to the Troubleshooting section.

**Happy Trading! 📈**

