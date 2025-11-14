# 🚀 Complete Deployment Guide - Go Backend + Frontend

This guide will help you deploy your **NSE Stock Screener** (Go backend + static frontend) to a production server. Coming from Django/Python? No worries - we'll guide you through Go deployment step by step!

## 📋 Table of Contents

1. [Deployment Options](#deployment-options)
2. [Traditional VPS Deployment (Recommended for Beginners)](#traditional-vps-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Platform Deployment](#cloud-platform-deployment)
5. [Post-Deployment Checklist](#post-deployment-checklist)

---

## 🎯 Deployment Options

### Option 1: Traditional VPS (Like Django with Gunicorn + Nginx)
**Best for:** Beginners, full control, similar to Django deployment
- **Platforms:** DigitalOcean, Linode, AWS EC2, Hetzner
- **Cost:** ~$5-10/month
- **Difficulty:** Easy (similar to Django)

### Option 2: Docker Container
**Best for:** Consistency, scalability, modern deployment
- **Platforms:** Any VPS, AWS ECS, Google Cloud Run
- **Cost:** ~$5-15/month
- **Difficulty:** Medium

### Option 3: Platform as a Service
**Best for:** Zero DevOps, automatic scaling
- **Platforms:** Railway, Render, Fly.io
- **Cost:** ~$0-20/month
- **Difficulty:** Easy

---

# Traditional VPS Deployment

This is the most common approach and similar to deploying Django with Gunicorn + Nginx.

## Prerequisites

- Ubuntu 22.04 LTS VPS (2GB RAM, 20GB disk recommended)
- Domain name (optional but recommended)
- SSH access to server
- Basic Linux command knowledge

---

## Step 1: Initial Server Setup

### 1.1 Connect to Your Server

```bash
ssh root@your-server-ip
```

### 1.2 Update System & Install Basic Tools

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl git build-essential ufw
```

### 1.3 Create a Deploy User (Security Best Practice)

```bash
# Create user
adduser deploy
usermod -aG sudo deploy

# Switch to deploy user
su - deploy
```

---

## Step 2: Install Go

**Unlike Python, Go needs to be installed manually on Ubuntu:**

```bash
# Download Go 1.21 (or latest version)
cd /tmp
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# Remove old Go installation (if any)
sudo rm -rf /usr/local/go

# Extract to /usr/local
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# Add Go to PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.profile
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.profile
source ~/.profile

# Verify installation
go version
# Should show: go version go1.21.5 linux/amd64
```

---

## Step 3: Install PostgreSQL

**Similar to Django's database setup:**

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE stock_trading;
CREATE USER trader WITH ENCRYPTED PASSWORD 'YourStrongPassword123!';
GRANT ALL PRIVILEGES ON DATABASE stock_trading TO trader;
\q
EOF

# Test connection
psql -h localhost -U trader -d stock_trading -W
# Enter password when prompted, then type \q to exit
```

---

## Step 4: Install Nginx

**Similar to serving Django static files and proxying to Gunicorn:**

```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

---

## Step 5: Upload Your Project

### Option A: Using Git (Recommended)

```bash
# Navigate to home directory
cd /home/deploy

# Clone your repository
git clone https://github.com/yourusername/get-uptrend-stocks.git
cd get-uptrend-stocks/nse-trend-stocks
```

### Option B: Using SCP/RSYNC (From Your Local Machine)

```bash
# From your local machine terminal:
cd /Users/farhanfm/Developer/personal/get-uptrend-stocks

# Upload files to server
rsync -avz --progress ./nse-trend-stocks/ deploy@your-server-ip:/home/deploy/nse-stock-platform/
```

---

## Step 6: Configure Environment Variables

```bash
cd /home/deploy/get-uptrend-stocks/nse-trend-stocks/backend-go

# Create .env file
nano .env
```

**Add the following configuration:**

```env
# Server Configuration
PORT=8000
GIN_MODE=release

# Database (Update with your actual password)
DATABASE_URL=postgresql://trader:YourStrongPassword123!@localhost:5432/stock_trading

# JWT Secret (Generate a strong key)
SECRET_KEY=your-super-secret-key-change-this-now
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Google OAuth (Optional - Configure in Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/api/v2/auth/google/callback

# Gemini AI (Optional - Get from Google AI Studio)
GEMINI_API_KEY=your-gemini-api-key

# Frontend URL
FRONTEND_URL=https://yourdomain.com

# Trading Configuration
COMMISSION_RATE=0.001
```

**Generate a strong SECRET_KEY:**

```bash
# Generate random key
openssl rand -base64 32
# Copy output and paste as SECRET_KEY in .env
```

**Secure the .env file:**

```bash
chmod 600 .env
```

---

## Step 7: Build Go Application

**This is different from Python! Go compiles to a single binary:**

```bash
cd /home/deploy/get-uptrend-stocks/nse-trend-stocks/backend-go

# Download dependencies
go mod download

# Build the application (creates a single binary)
go build -o nse-stock-screener main.go

# Test the binary
./nse-stock-screener
# Press Ctrl+C after seeing "Starting server on http://0.0.0.0:8000"
```

**Key Difference from Django/Python:**
- Django: Need Python interpreter + virtualenv + dependencies
- Go: Just one binary file (nse-stock-screener) - no dependencies needed!

---

## Step 8: Configure Nginx

**Similar to serving Django through Nginx:**

```bash
sudo nano /etc/nginx/sites-available/stock-platform
```

**Add this configuration:**

```nginx
# Stock Platform - Nginx Configuration

upstream go_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit
    client_max_body_size 10M;

    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Serve frontend static files (HTML, CSS, JS)
    location / {
        root /home/deploy/get-uptrend-stocks/nse-trend-stocks/frontend;
        try_files $uri $uri/ /index.html;
        index index.html;
        
        # Cache static assets
        location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # Proxy API requests to Go backend
    location /api/ {
        proxy_pass http://go_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**Enable the site:**

```bash
# Test configuration
sudo nginx -t

# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/stock-platform /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 9: Create Systemd Service

**This is similar to running Django with Gunicorn as a service:**

```bash
sudo nano /etc/systemd/system/stock-platform.service
```

**Add this configuration:**

```ini
[Unit]
Description=NSE Stock Screener - Go Backend
After=network.target postgresql.service

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/get-uptrend-stocks/nse-trend-stocks/backend-go

# Path to the Go binary
ExecStart=/home/deploy/get-uptrend-stocks/nse-trend-stocks/backend-go/nse-stock-screener

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stock-platform

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**Start the service:**

```bash
# Reload systemd to read new service file
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable stock-platform

# Start the service
sudo systemctl start stock-platform

# Check status
sudo systemctl status stock-platform
```

**View logs:**

```bash
# Follow logs in real-time
sudo journalctl -u stock-platform -f

# View last 50 lines
sudo journalctl -u stock-platform -n 50

# View today's logs
sudo journalctl -u stock-platform --since today
```

---

## Step 10: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP
sudo ufw allow 80/tcp

# Allow HTTPS
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Step 11: Setup SSL/HTTPS (Let's Encrypt)

**Free SSL certificate using Certbot:**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Test auto-renewal
sudo certbot renew --dry-run
```

**Certificates will auto-renew via cron job!**

---

## Step 12: Verify Deployment

### Test Backend

```bash
# Test locally on server
curl http://localhost:8000/api/v2/health

# Test through Nginx
curl http://localhost/api/v2/health

# Test from outside (replace with your domain/IP)
curl https://yourdomain.com/api/v2/health
```

### Test Frontend

Open browser and visit:
- `https://yourdomain.com` - Should show your frontend
- `https://yourdomain.com/api/v2/health` - Should return `{"status":"healthy"}`

### Create First User

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

---

## Step 13: Setup Database Backups

```bash
# Create backup script
nano ~/backup-database.sh
```

**Add:**

```bash
#!/bin/bash
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="stock_trading_$DATE.sql"

mkdir -p $BACKUP_DIR

# Backup database
PGPASSWORD='YourStrongPassword123!' pg_dump -U trader -h localhost stock_trading > "$BACKUP_DIR/$FILENAME"

# Compress backup
gzip "$BACKUP_DIR/$FILENAME"

# Keep only last 7 days
find $BACKUP_DIR -name "stock_trading_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $FILENAME.gz"
```

**Make executable and schedule:**

```bash
chmod +x ~/backup-database.sh

# Test backup
~/backup-database.sh

# Schedule daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * /home/deploy/backup-database.sh >> /home/deploy/backup.log 2>&1
```

---

## 🔄 Updating Your Application

### Update Code and Rebuild

```bash
# Navigate to project
cd /home/deploy/get-uptrend-stocks/nse-trend-stocks

# Pull latest changes
git pull origin main

# Navigate to backend
cd backend-go

# Rebuild binary
go build -o nse-stock-screener main.go

# Restart service
sudo systemctl restart stock-platform

# Check logs
sudo journalctl -u stock-platform -f
```

**Key Difference from Django:**
- Django: Just restart service (code is interpreted)
- Go: Must rebuild binary, then restart service

---

# 🐳 Docker Deployment

**Alternative deployment using Docker - simpler and more portable!**

## Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install -y docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Deploy with Docker Compose

```bash
# Navigate to backend directory
cd /home/deploy/get-uptrend-stocks/nse-trend-stocks/backend-go

# Create .env file (same as Step 6 above)
nano .env

# Start services (backend + PostgreSQL)
docker-compose up -d

# View logs
docker-compose logs -f

# Check running containers
docker ps
```

## Nginx Configuration for Docker

Update Nginx upstream to use Docker container:

```nginx
upstream go_backend {
    server 127.0.0.1:8000;  # Docker exposes on port 8000
}
```

## Useful Docker Commands

```bash
# View logs
docker-compose logs -f app

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View running containers
docker ps

# Execute commands in container
docker-compose exec app sh
```

---

# ☁️ Cloud Platform Deployment

## Deploying to Railway (Easiest)

**Railway is like Heroku but better and supports Go out of the box!**

### 1. Install Railway CLI

```bash
npm i -g @railway/cli
```

### 2. Login and Initialize

```bash
cd /Users/farhanfm/Developer/personal/get-uptrend-stocks/nse-trend-stocks/backend-go

railway login
railway init
```

### 3. Create PostgreSQL Database

In Railway dashboard:
1. Create new project
2. Add PostgreSQL database
3. Copy DATABASE_URL

### 4. Set Environment Variables

```bash
railway variables set SECRET_KEY="your-secret-key"
railway variables set GIN_MODE="release"
# Add other variables from .env
```

### 5. Deploy

```bash
railway up
```

**Railway will automatically:**
- Detect Go application
- Build the binary
- Deploy to production
- Give you a public URL

### 6. Deploy Frontend

Use **Netlify** or **Vercel** for frontend (both have free tiers):

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Navigate to frontend
cd ../frontend

# Deploy
netlify deploy --prod
```

---

## Deploying to Render

**Render offers free tier for Go apps!**

### 1. Push to GitHub

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Create Web Service on Render.com

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Configure:
   - **Name:** nse-stock-screener
   - **Environment:** Go
   - **Build Command:** `cd nse-trend-stocks/backend-go && go build -o main main.go`
   - **Start Command:** `cd nse-trend-stocks/backend-go && ./main`
   - **Instance Type:** Free (or paid for better performance)

### 3. Add Environment Variables

In Render dashboard, add all variables from your .env file.

### 4. Add PostgreSQL

1. Click "New +" → "PostgreSQL"
2. Copy connection string
3. Add as DATABASE_URL in web service

### 5. Deploy Frontend

Use **Render Static Site** or **Netlify** for frontend.

---

# 📋 Post-Deployment Checklist

## Security

- [ ] Strong database password set
- [ ] SECRET_KEY is random and secure
- [ ] Firewall configured (ufw)
- [ ] SSL/HTTPS enabled
- [ ] .env file has chmod 600
- [ ] SSH key authentication enabled (disable password auth)
- [ ] Regular backups configured
- [ ] Google OAuth credentials secured

## Monitoring

- [ ] Application logs accessible (`journalctl`)
- [ ] Nginx logs accessible (`/var/log/nginx/`)
- [ ] Database backups working
- [ ] Disk space monitoring (`df -h`)
- [ ] Memory usage monitoring (`free -h`)

## Functionality

- [ ] Frontend loads correctly
- [ ] API health check works
- [ ] User registration works
- [ ] User login works
- [ ] Stock screening works
- [ ] Trading operations work
- [ ] Google OAuth works (if configured)

---

# 🔧 Troubleshooting

## Backend Not Starting

```bash
# Check service status
sudo systemctl status stock-platform

# View logs
sudo journalctl -u stock-platform -n 50

# Check if port is in use
sudo lsof -i :8000

# Test binary manually
cd /home/deploy/get-uptrend-stocks/nse-trend-stocks/backend-go
./nse-stock-screener
```

## Database Connection Failed

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U trader -d stock_trading -W

# Check logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

## Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Check access logs
sudo tail -f /var/log/nginx/access.log

# Restart Nginx
sudo systemctl restart nginx
```

## Go Binary Crashes

```bash
# Check system resources
free -h
df -h

# Check for missing dependencies
ldd ./nse-stock-screener

# View detailed logs
sudo journalctl -u stock-platform -f
```

## 502 Bad Gateway

This usually means Nginx can't connect to Go backend:

```bash
# Is the Go service running?
sudo systemctl status stock-platform

# Is it listening on port 8000?
sudo netstat -tlnp | grep 8000

# Check Nginx upstream configuration
sudo nginx -t
```

---

# 🚀 Performance Tips

## 1. Enable HTTP/2 in Nginx

```nginx
listen 443 ssl http2;
```

## 2. Add Caching Headers

```nginx
location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 3. Use Connection Pooling (Already configured in database.go)

The Go backend uses GORM with connection pooling - make sure these are set:

```go
sqlDB.SetMaxOpenConns(25)
sqlDB.SetMaxIdleConns(5)
sqlDB.SetConnMaxLifetime(5 * time.Minute)
```

## 4. Add Database Indexes

```sql
-- Connect to database
sudo -u postgres psql stock_trading

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_trades_user_created ON trades(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_user ON watchlists(user_id);
```

---

# 📊 Monitoring & Logs

## View Application Logs

```bash
# Real-time logs
sudo journalctl -u stock-platform -f

# Last 100 lines
sudo journalctl -u stock-platform -n 100

# Errors only
sudo journalctl -u stock-platform -p err

# Today's logs
sudo journalctl -u stock-platform --since today
```

## System Resources

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Database size
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('stock_trading'));"
```

---

# 🎉 Congratulations!

Your NSE Stock Screener is now deployed! 

**Key URLs:**
- Frontend: `https://yourdomain.com`
- API Root: `https://yourdomain.com/api/v2/`
- Health Check: `https://yourdomain.com/api/v2/health`

## Next Steps

1. **Setup monitoring** (optional): Consider using Uptime Robot or Sentry
2. **Configure Google OAuth**: Set up OAuth credentials in Google Cloud Console
3. **Add Gemini AI**: Get API key from Google AI Studio for AI analysis
4. **Optimize performance**: Add Redis caching if needed
5. **Scale up**: Add more server resources as user base grows

---

# 📚 Additional Resources

- **Go Documentation:** https://go.dev/doc/
- **Gin Framework:** https://gin-gonic.com/docs/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **Nginx:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/docs/

---

# 🆘 Need Help?

If you encounter issues:
1. Check the **Troubleshooting** section above
2. Review application logs
3. Check Nginx error logs
4. Verify database connection
5. Ensure all environment variables are set correctly

**Happy Trading! 📈**
