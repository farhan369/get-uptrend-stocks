# 🚀 Quick Start Guide - UpwardStocks Platform

Get up and running in 15 minutes!

## ✅ What's Included

✨ **Complete Authentication System**
- Email/Password registration and login
- **Google OAuth 2.0 Sign-In** (Single Sign-On)
- JWT-based secure authentication
- User profile management

📊 **Advanced Stock Screening**
- 120-point technical analysis system
- Real-time NSE stock data
- AI-powered insights with Google Gemini
- Multiple screening presets

💰 **Paper Trading Platform**
- ₹10 Lakh virtual capital
- Real-time portfolio tracking
- P&L calculation
- Trade history

🎨 **Modern Frontend**
- Responsive Vue.js interface
- Google OAuth integration
- Dashboard and screening pages
- Mobile-friendly design

---

## 📦 Project Structure

```
nse-trend-stocks/
├── backend/              # FastAPI backend
│   ├── main.py          # Main application
│   ├── auth.py          # JWT authentication
│   ├── google_auth.py   # Google OAuth
│   ├── models.py        # Database models
│   └── ...
├── frontend/            # Vue.js frontend (NEW!)
│   ├── index.html       # Login page
│   ├── register.html    # Registration
│   ├── dashboard.html   # User dashboard
│   └── screener.html    # Stock screener
└── DEPLOYMENT.md        # Full deployment guide
```

---

## ⚡ Local Development Setup

### Step 1: Install Dependencies

```bash
# Backend
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requiewments.txt
```

### Step 2: Setup PostgreSQL

```bash
# Install PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb stock_trading
psql stock_trading -c "CREATE USER trader WITH PASSWORD 'password';"
psql stock_trading -c "GRANT ALL ON DATABASE stock_trading TO trader;"
```

### Step 3: Configure Environment

```bash
cd backend
cp .env.example .env  # If it exists, otherwise create .env
nano .env
```

**Minimal .env configuration:**

```env
# Database
DATABASE_URL=postgresql://trader:password@localhost:5432/stock_trading

# Security (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-generated-secret-key-here

# Optional: Gemini AI
GEMINI_API_KEY=your-gemini-api-key

# Optional: Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v2/auth/google/callback
FRONTEND_URL=/static
```

### Step 4: Start Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

You should see:
```
✓ Database initialized successfully
✓ Frontend static files mounted
✓ Google OAuth configured successfully (if configured)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Access the Application

Open your browser and go to:
- **Frontend**: http://localhost:8000/static/index.html
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/static/dashboard.html (after login)

---

## 🔐 Google OAuth Setup (Optional)

If you want to enable "Sign in with Google":

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/v2/auth/google/callback`
5. Copy Client ID and Client Secret to `.env`

**Detailed guide**: See [backend/GOOGLE_OAUTH_SETUP.md](backend/GOOGLE_OAUTH_SETUP.md)

---

## 🌐 Production Deployment

### Option 1: Single Server (Recommended)

Deploy both frontend and backend on one server using Nginx.

**Quick Steps:**

```bash
# 1. Setup server
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 postgresql nginx

# 2. Upload code
scp -r ./nse-trend-stocks user@your-server:/home/user/

# 3. Configure (follow DEPLOYMENT.md)
# - Setup PostgreSQL
# - Configure Nginx
# - Setup SSL with Certbot
# - Create systemd service

# 4. Access
https://yourdomain.com
```

**Full Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

### Option 2: Separate Servers

- Backend: Deploy to DigitalOcean/AWS with Nginx
- Frontend: Deploy to Netlify/Vercel
- Database: Managed PostgreSQL (AWS RDS, DigitalOcean Managed DB)

---

## 📝 First Time Setup

### 1. Create Your First Account

**Option A: Email/Password**
1. Go to http://localhost:8000/static/register.html
2. Fill in your details
3. Click "Create Account"
4. You'll be redirected to the dashboard

**Option B: Google OAuth**
1. Go to http://localhost:8000/static/index.html
2. Click "Continue with Google"
3. Authenticate with Google
4. You'll be redirected to the dashboard

### 2. Start Using the Platform

**Screen Stocks:**
1. Navigate to "Stock Screener" from dashboard
2. Use preset strategies or customize filters
3. Click "Screen Stocks"
4. View results with 120-point scores

**AI Analysis:**
1. Enter a stock symbol (e.g., RELIANCE)
2. Click "Analyze"
3. Get comprehensive AI-powered insights

**Paper Trading:**
- Feature coming soon in dashboard!

---

## 🎯 API Endpoints

### Authentication
```bash
# Register
POST /api/v2/auth/register
Body: {"email": "user@example.com", "username": "user", "password": "password123"}

# Login
POST /api/v2/auth/login
Body: username=user&password=password123

# Google OAuth
GET /api/v2/auth/google/login
GET /api/v2/auth/google/callback

# Get Current User
GET /api/v2/auth/me
Headers: Authorization: Bearer <token>
```

### Stock Screening
```bash
# Screen Stocks
POST /api/v2/stocks/screen
Body: {"min_score": 80, "min_adx": 30}

# Get Stock Details
GET /api/v2/stock/RELIANCE

# AI Analysis
GET /api/v2/stock/RELIANCE/analyze
```

### Paper Trading
```bash
# Get Dashboard
GET /api/v2/trading/dashboard
Headers: Authorization: Bearer <token>

# Execute Trade
POST /api/v2/trading/trade
Headers: Authorization: Bearer <token>
Body: {"symbol": "RELIANCE", "order_side": "BUY", "quantity": 10}

# Get Portfolio
GET /api/v2/trading/portfolio
Headers: Authorization: Bearer <token>
```

**Full API Documentation**: http://localhost:8000/docs

---

## 🐛 Troubleshooting

### Backend won't start

**Error: Database connection failed**
```bash
# Check PostgreSQL is running
brew services list | grep postgresql
# or
sudo systemctl status postgresql

# Test connection
psql -U trader -d stock_trading
```

**Error: Module not found**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requiewments.txt
```

### Frontend not loading

**404 Error on /static/index.html**
```bash
# Check if frontend folder exists
ls -la ../frontend/

# Verify backend logs
python main.py
# Look for: "✓ Frontend static files mounted"
```

### Google OAuth not working

**Error: redirect_uri_mismatch**
- Check GOOGLE_REDIRECT_URI in `.env` matches Google Cloud Console exactly
- Make sure no trailing slashes

**Error: Google OAuth is not configured**
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set in `.env`
- Restart backend after changing `.env`

### Database errors

**Error: relation "users" does not exist**
```bash
# Database tables not created
# Run backend once to initialize
python main.py
# Press Ctrl+C after seeing "Database initialized"
```

---

## 📚 Documentation

- **[README.md](backend/README.md)** - Project overview and features
- **[SETUP.md](backend/SETUP.md)** - Detailed setup instructions
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[GOOGLE_OAUTH_SETUP.md](backend/GOOGLE_OAUTH_SETUP.md)** - Google OAuth setup
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Code organization
- **API Docs** - http://localhost:8000/docs (when running)

---

## 🎓 Usage Examples

### Example 1: Screen High-Momentum Stocks

```javascript
// Using JavaScript/Axios
const filters = {
    min_score: 80,
    min_adx: 30,
    rsi_min: 60,
    rsi_max: 75
};

axios.post('http://localhost:8000/api/v2/stocks/screen', filters)
    .then(response => {
        console.log('Found stocks:', response.data.results);
    });
```

### Example 2: Get AI Analysis

```bash
# Using curl
curl "http://localhost:8000/api/v2/stock/TCS/analyze"
```

### Example 3: Execute Trade

```javascript
// Using JavaScript with auth token
const tradeData = {
    symbol: "RELIANCE",
    order_side: "BUY",
    quantity: 10,
    order_type: "MARKET"
};

axios.post('http://localhost:8000/api/v2/trading/trade', tradeData, {
    headers: { 'Authorization': `Bearer ${token}` }
})
.then(response => {
    console.log('Trade executed:', response.data);
});
```

---

## 🔄 Updating the Application

```bash
# Pull latest changes
git pull origin main

# Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requiewments.txt --upgrade

# Restart (if using systemd in production)
sudo systemctl restart stock-platform

# Or restart manually (development)
# Press Ctrl+C and run: python main.py
```

---

## ⚙️ Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| DATABASE_URL | Yes | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| SECRET_KEY | Yes | JWT signing key (32+ chars) | `your-secret-key-here` |
| GEMINI_API_KEY | No | Google Gemini API key | `AIza...` |
| GOOGLE_CLIENT_ID | No | Google OAuth client ID | `123-abc.apps.googleusercontent.com` |
| GOOGLE_CLIENT_SECRET | No | Google OAuth secret | `GOCSPX-...` |
| GOOGLE_REDIRECT_URI | No | OAuth callback URL | `http://localhost:8000/api/v2/auth/google/callback` |
| FRONTEND_URL | No | Frontend URL for redirects | `/static` or `https://yourdomain.com` |

---

## 🎉 You're All Set!

Your UpwardStocks Platform is now running with:

✅ Full authentication system (email + Google OAuth)  
✅ Advanced stock screening with 120-point analysis  
✅ AI-powered insights  
✅ Paper trading capabilities  
✅ Modern responsive UI  
✅ Production-ready architecture  

**Next Steps:**
1. Explore the stock screener
2. Try AI analysis on different stocks
3. Customize the frontend to match your brand
4. Deploy to production following DEPLOYMENT.md
5. Add your own features!

**Need Help?**
- Check the documentation files
- Review API docs at /docs
- Check troubleshooting section above

**Happy Trading! 📈**

