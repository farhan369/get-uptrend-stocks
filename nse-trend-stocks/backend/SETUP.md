# Quick Setup Guide

## Step-by-Step Setup

### 1. Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download from: https://www.postgresql.org/download/windows/

### 2. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# In psql:
CREATE DATABASE stock_trading;
CREATE USER trader WITH ENCRYPTED PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE stock_trading TO trader;
\q
```

### 3. Setup Environment Variables

Create `.env` file in the backend directory:

```env
# Copy this to .env file
DATABASE_URL=postgresql://trader:yourpassword@localhost:5432/stock_trading
SECRET_KEY=<generate-a-secret-key-see-below>
GEMINI_API_KEY=<optional-for-ai-features>

# Google OAuth (Optional - for Google Sign-In)
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v2/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.1 Configure Google OAuth (Optional)

If you want to enable Google Sign-In:

1. **Go to Google Cloud Console:**
   - Visit https://console.cloud.google.com/

2. **Create a new project (or select existing):**
   - Click "Select a project" → "New Project"
   - Name it (e.g., "Stock Trading App")
   - Click "Create"

3. **Enable Google+ API:**
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click and enable it

4. **Create OAuth 2.0 Credentials:**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://localhost:8000/api/v2/auth/google/callback` (for local development)
     - `https://yourdomain.com/api/v2/auth/google/callback` (for production)
   - Click "Create"

5. **Copy credentials to .env:**
   - Copy the "Client ID" to `GOOGLE_CLIENT_ID`
   - Copy the "Client secret" to `GOOGLE_CLIENT_SECRET`

**Note:** Google OAuth is optional. The app works fine with email/password authentication if you don't configure it.

**Get Gemini API Key (Optional for AI features):**
1. Visit https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy and paste into .env

### 4. Install Python Dependencies

```bash
cd nse-trend-stocks/backend

# Activate virtual environment (if not already activated)
source ../nse-stock-up-trend/bin/activate

# Install packages
pip install -r requiewments.txt
```

### 5. Run the Server

```bash
python main.py
```

You should see:
```
✓ Database initialized successfully
✓ Gemini AI configured successfully
Starting server on http://0.0.0.0:8000
```

### 6. Test the API

Open browser: http://localhost:8000/docs

Or test with curl:
```bash
# Health check
curl http://localhost:8000/api/v2/health

# Test data fetching
curl http://localhost:8000/api/v2/test-fetch/RELIANCE
```

### 7. Create Your First User

**Using API Docs** (Easiest):
1. Go to http://localhost:8000/docs
2. Find `POST /api/v2/auth/register`
3. Click "Try it out"
4. Enter:
```json
{
  "email": "your@email.com",
  "username": "yourname",
  "password": "yourpassword123",
  "full_name": "Your Name"
}
```
5. Click "Execute"
6. Copy the `access_token` from the response

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trader@example.com",
    "username": "trader1",
    "password": "mypassword123",
    "full_name": "John Trader"
  }'
```

### 8. Start Trading!

You now have ₹10,00,000 (10 lakhs) in your account.

**Buy your first stock:**
```bash
curl -X POST "http://localhost:8000/api/v2/trading/trade" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "order_side": "BUY",
    "order_type": "MARKET",
    "quantity": 10,
    "notes": "First trade!"
  }'
```

**Check your portfolio:**
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/v2/trading/portfolio
```

### 9. Open Frontend

Navigate to frontend directory and open `index.html`:

```bash
cd ../front-end
open index.html  # macOS
# or
xdg-open index.html  # Linux
# or just double-click index.html on Windows
```

## Common Issues & Solutions

### Issue: Database Connection Failed

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@14  # macOS

# Test connection
psql -U trader -d stock_trading
```

### Issue: ModuleNotFoundError

**Solution:**
```bash
# Make sure virtual environment is activated
source ../nse-stock-up-trend/bin/activate

# Reinstall dependencies
pip install --force-reinstall -r requiewments.txt
```

### Issue: yfinance not fetching data

**Solution:**
```bash
# Upgrade yfinance
pip install --upgrade yfinance

# Test specific stock
curl http://localhost:8000/api/v2/test-fetch/TCS
```

### Issue: JWT Token Expired

**Solution:**
Just login again to get a new token. Tokens expire after 7 days.

```bash
curl -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=trader1&password=mypassword123"
```

## Quick Commands Reference

```bash
# Start server
python main.py

# Create user
curl -X POST http://localhost:8000/api/v2/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"test","password":"test123"}'

# Login
curl -X POST http://localhost:8000/api/v2/auth/login \
  -d "username=test&password=test123"

# Screen stocks
curl -X POST http://localhost:8000/api/v2/stocks/screen \
  -H "Content-Type: application/json" \
  -d '{"min_score": 70}'

# Buy stock
curl -X POST http://localhost:8000/api/v2/trading/trade \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"TCS","order_side":"BUY","quantity":5}'

# View portfolio
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v2/trading/portfolio

# View positions
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v2/trading/positions

# Trade history
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v2/trading/trades
```

## Next Steps

1. ✅ Register an account
2. ✅ Explore the stock screener (no auth required)
3. ✅ Execute your first paper trade
4. ✅ Build your watchlist
5. ✅ Try the AI analysis feature
6. ✅ Track your portfolio performance

## Need Help?

- API Documentation: http://localhost:8000/docs
- Check server logs for detailed error messages
- Ensure `.env` file has correct database URL
- Make sure PostgreSQL is running

Happy Trading! 🚀📈

