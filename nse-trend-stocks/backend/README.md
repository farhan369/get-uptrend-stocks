# NSE Stock Screener with Paper Trading Platform

A comprehensive stock screening and paper trading platform with advanced technical analysis, AI-powered insights, and full portfolio management.

## Features

### 📊 Advanced Stock Screening
- 120-point technical analysis scoring system
- Comprehensive indicators: RSI, MACD, ADX, Bollinger Bands, OBV, etc.
- Multiple filtering options and preset strategies
- Real-time data from NSE via yfinance

### 🤖 AI-Powered Analysis
- Google Gemini AI integration for detailed stock analysis
- Technical health assessment
- Risk evaluation and trading strategy recommendations
- Fundamental perspective and investment ratings

### 💰 Paper Trading Platform
- Virtual trading with ₹10 lakh starting capital
- Real-time position tracking and P&L calculation
- Market, Limit, and Stop-Loss order types
- Complete trade history and portfolio analytics
- Watchlist management with price alerts

### 🔐 Secure Authentication
- JWT-based authentication system
- **Google OAuth 2.0 Sign-In** (Single Sign-On)
- Traditional email/password authentication
- Secure password hashing with bcrypt
- User-specific portfolios and data isolation
- Support for OAuth-linked and password-based accounts

## Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with python-jose
- **Financial Data**: yfinance
- **Analysis**: pandas, numpy
- **AI**: Google Gemini API
- **Frontend**: Vue.js 3 with Tailwind CSS

## Setup Instructions

### 1. Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+ installed and running
- Git

### 2. Clone the Repository

```bash
cd get-uptrend-stocks/nse-trend-stocks/backend
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requiewments.txt
```

### 5. Setup PostgreSQL Database

**Create Database:**

```bash
psql -U postgres
CREATE DATABASE stock_trading;
\q
```

Or using pgAdmin or any PostgreSQL client.

### 6. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/stock_trading
SECRET_KEY=your-super-secret-key-minimum-32-characters-long
GEMINI_API_KEY=your-gemini-api-key  # Optional for AI features

# Google OAuth (Optional - for Google Sign-In)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v2/auth/google/callback
FRONTEND_URL=http://localhost:3000
```

> **Note:** For detailed Google OAuth setup instructions, see [SETUP.md](SETUP.md#31-configure-google-oauth-optional)

**Generate a secure SECRET_KEY:**

```python
import secrets
print(secrets.token_urlsafe(32))
```

**Get Gemini API Key (Optional):**
- Visit: https://aistudio.google.com/app/apikey
- Create a new API key
- Add it to your `.env` file

### 7. Run the Server

```bash
python main.py
```

The server will start at `http://localhost:8000`

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

### 8. Open Frontend

Open `../front-end/index.html` in your browser or serve it with a local server:

```bash
cd ../front-end
python -m http.server 8080
```

Then visit: http://localhost:8080

## Database Schema

The application automatically creates all necessary tables on startup:

- **users**: User accounts with authentication
- **portfolios**: User portfolios with cash and holdings
- **positions**: Current stock holdings
- **trades**: Complete trade history
- **watchlists**: User watchlists with price alerts
- **portfolio_snapshots**: Historical portfolio performance

## API Endpoints

### Authentication
- `POST /api/v2/auth/register` - Register new user
- `POST /api/v2/auth/login` - Login and get JWT token
- `GET /api/v2/auth/me` - Get current user info
- `GET /api/v2/auth/google/login` - Initiate Google OAuth login
- `GET /api/v2/auth/google/callback` - Google OAuth callback

### Stock Screening
- `POST /api/v2/stocks/screen` - Screen stocks with filters
- `GET /api/v2/stock/{symbol}` - Get stock details
- `GET /api/v2/stock/{symbol}/analyze` - AI analysis
- `GET /api/v2/sectors` - Get available sectors
- `GET /api/v2/presets` - Get screening presets

### Paper Trading
- `GET /api/v2/trading/dashboard` - Complete dashboard
- `GET /api/v2/trading/portfolio` - Portfolio summary
- `POST /api/v2/trading/trade` - Execute trade
- `GET /api/v2/trading/positions` - Current positions
- `GET /api/v2/trading/trades` - Trade history
- `POST /api/v2/trading/watchlist` - Add to watchlist
- `GET /api/v2/trading/watchlist` - Get watchlist
- `DELETE /api/v2/trading/watchlist/{id}` - Remove from watchlist

## Usage Examples

### Register and Login

```bash
# Register
curl -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trader@example.com",
    "username": "trader1",
    "password": "securepass123",
    "full_name": "John Trader"
  }'

# Login
curl -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=trader1&password=securepass123"
```

### Google OAuth Login

For web applications, redirect users to:
```
http://localhost:8000/api/v2/auth/google/login
```

The flow:
1. User clicks "Sign in with Google"
2. Browser redirects to `/api/v2/auth/google/login`
3. User authenticates with Google
4. Google redirects back to `/api/v2/auth/google/callback`
5. Backend creates/updates user and returns JWT token
6. Frontend stores token and redirects to dashboard

Example JavaScript implementation:
```javascript
// Frontend: Initiate Google login
function loginWithGoogle() {
  window.location.href = 'http://localhost:8000/api/v2/auth/google/login';
}

// Frontend: Handle callback (on your callback page)
async function handleGoogleCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');
  
  if (token) {
    localStorage.setItem('access_token', token);
    // Redirect to dashboard
    window.location.href = '/dashboard';
  }
}
```

### Execute a Trade

```bash
# Buy 10 shares of RELIANCE at market price
curl -X POST "http://localhost:8000/api/v2/trading/trade" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "RELIANCE",
    "order_side": "BUY",
    "order_type": "MARKET",
    "quantity": 10
  }'
```

### Screen Stocks

```bash
# Find high-momentum stocks
curl -X POST "http://localhost:8000/api/v2/stocks/screen" \
  -H "Content-Type: application/json" \
  -d '{
    "min_score": 80,
    "min_adx": 30,
    "rsi_min": 60,
    "rsi_max": 75
  }'
```

## Development

### Database Migrations (Future)

If you make changes to models, you can use Alembic for migrations:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### Testing

```bash
# Test data fetching
curl http://localhost:8000/api/v2/test-fetch/RELIANCE

# Check health
curl http://localhost:8000/api/v2/health
```

## Production Deployment

### Environment Variables

Set these in production:

```env
DATABASE_URL=postgresql://user:pass@prod-db-host:5432/stock_trading
SECRET_KEY=very-long-random-secure-key-from-secrets-manager
GEMINI_API_KEY=prod-gemini-key
```

### Security Recommendations

1. Use a strong, randomly generated `SECRET_KEY`
2. Enable HTTPS/SSL for database connections
3. Use environment variables for all secrets
4. Enable PostgreSQL SSL mode
5. Set up proper firewall rules
6. Use a reverse proxy (nginx/traefik)
7. Enable CORS only for your frontend domain

### Docker Deployment (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requiewments.txt .
RUN pip install --no-cache-dir -r requiewments.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Run with docker-compose:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: stock_trading
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/stock_trading
      SECRET_KEY: your-secret-key
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo service postgresql status

# Check connection
psql -U postgres -d stock_trading
```

### yfinance Data Issues

```bash
# Upgrade yfinance
pip install --upgrade yfinance

# Test individual stock
curl http://localhost:8000/api/v2/test-fetch/RELIANCE
```

### Import Errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requiewments.txt
```

## Performance Optimization

- **Caching**: Stock data is cached for 1 hour
- **Batch Fetching**: Stocks are fetched in batches to reduce API calls
- **Database Indexing**: All key fields are indexed
- **Connection Pooling**: SQLAlchemy connection pool configured

## License

MIT License - feel free to use for personal or commercial projects

## Support

For issues or questions:
1. Check the API docs at http://localhost:8000/docs
2. Review the logs for error messages
3. Ensure all environment variables are set correctly

## Future Enhancements

- [ ] Real-time WebSocket price updates
- [ ] Advanced charting with technical indicators
- [ ] Backtesting framework
- [ ] Email/SMS price alerts
- [ ] Social features (share trades, leaderboards)
- [ ] Mobile app (React Native)
- [ ] Options trading simulation
- [ ] News sentiment analysis
- [ ] Portfolio optimization algorithms

---

Built with ❤️ for Indian stock traders

