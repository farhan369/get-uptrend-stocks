# Project Structure - NSE Stock Trading Platform

This document outlines the improved folder structure and organization of the codebase for better maintainability and deployment.

## 📁 Directory Structure

```
nse-trend-stocks/
├── backend/                          # Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py                       # Main application entry point
│   ├── auth.py                       # JWT authentication utilities
│   ├── google_auth.py                # Google OAuth implementation
│   ├── database.py                   # Database connection & setup
│   ├── models.py                     # SQLAlchemy ORM models
│   ├── schemas.py                    # Pydantic validation schemas
│   ├── trading_engine.py             # Paper trading logic
│   ├── requiewments.txt              # Python dependencies
│   ├── .env                          # Environment variables (git-ignored)
│   ├── .env.example                  # Environment template
│   ├── README.md                     # Backend documentation
│   ├── SETUP.md                      # Setup instructions
│   └── GOOGLE_OAUTH_SETUP.md         # Google OAuth setup guide
│
├── frontend/                         # Frontend (Vue.js 3 + Vanilla JS)
│   ├── index.html                    # Login page
│   ├── register.html                 # Registration page
│   ├── auth-callback.html            # OAuth callback handler
│   ├── auth-success.html             # OAuth success handler
│   ├── dashboard.html                # User dashboard
│   ├── screener.html                 # Stock screener page
│   ├── css/
│   │   └── styles.css                # Custom styles
│   └── js/
│       ├── config.js                 # API configuration
│       └── auth.js                   # Authentication utilities
│
├── front-end/                        # Old frontend (deprecated)
│   └── index.html                    # Legacy screening page
│
├── nse-stock-up-trend/               # Python virtual environment
│   ├── bin/
│   ├── include/
│   ├── lib/
│   └── pyvenv.cfg
│
├── DEPLOYMENT.md                     # Single-server deployment guide
└── PROJECT_STRUCTURE.md              # This file
```

---

## 🔧 Backend Structure

### Core Files

#### `main.py`
- **Purpose**: Main FastAPI application
- **Responsibilities**:
  - API routes definition
  - Stock screening logic
  - Technical analysis engine
  - AI analysis integration (Gemini)
  - Static file serving for frontend

#### `auth.py`
- **Purpose**: Authentication and authorization
- **Functions**:
  - JWT token generation and validation
  - Password hashing (bcrypt)
  - User authentication
  - Protected route dependencies

#### `google_auth.py`
- **Purpose**: Google OAuth 2.0 integration
- **Functions**:
  - OAuth flow management
  - Google user info fetching
  - User creation/linking with Google accounts
  - Token generation for OAuth users

#### `database.py`
- **Purpose**: Database connection and initialization
- **Features**:
  - SQLAlchemy engine setup
  - Session management
  - Table creation

#### `models.py`
- **Purpose**: Database ORM models
- **Models**:
  - `User` - User accounts (supports both password and OAuth)
  - `Portfolio` - User portfolios
  - `Position` - Current stock holdings
  - `Trade` - Trade history
  - `Watchlist` - Stock watchlists
  - `PortfolioSnapshot` - Historical performance

#### `schemas.py`
- **Purpose**: Pydantic schemas for request/response validation
- **Schemas**:
  - User schemas (Create, Login, Response)
  - Portfolio schemas
  - Trade schemas
  - Position schemas
  - Watchlist schemas

#### `trading_engine.py`
- **Purpose**: Paper trading implementation
- **Features**:
  - Order execution (Market, Limit, Stop-Loss)
  - Position management
  - P&L calculation
  - Portfolio value updates

---

## 🎨 Frontend Structure

### Pages

#### `index.html` (Login Page)
- Email/password login
- Google OAuth button
- Link to registration
- Feature highlights

#### `register.html` (Registration Page)
- User registration form
- Google OAuth option
- Input validation
- Benefits list

#### `auth-callback.html` (OAuth Callback)
- Handles OAuth redirects
- Error display
- Loading state

#### `auth-success.html` (OAuth Success)
- Token extraction from URL
- User info fetching
- Dashboard redirect

#### `dashboard.html` (User Dashboard)
- Portfolio summary
- Current positions
- Recent trades
- Quick actions
- Navigation menu

#### `screener.html` (Stock Screener)
- 120-point technical analysis
- Advanced filters
- AI-powered analysis
- Stock screening results
- Export functionality

### Utilities

#### `js/config.js`
- API URL configuration
- Environment detection
- Auto-configuration for dev/prod

#### `js/auth.js`
- Token management
- User info storage
- Authentication check
- Logout function
- Axios interceptors

#### `css/styles.css`
- Custom animations
- Loading spinners
- Modal styles
- Responsive utilities
- Scrollbar styling

---

## 🗄️ Database Schema

### Users Table
```sql
- id (PK)
- email (unique)
- username (unique)
- hashed_password (nullable for OAuth users)
- full_name
- is_active
- is_verified
- oauth_provider (google, github, etc.)
- oauth_id (provider's user ID)
- profile_picture (URL)
- created_at
- updated_at
```

### Portfolios Table
```sql
- id (PK)
- user_id (FK)
- name
- cash_balance
- initial_balance
- total_invested
- total_profit_loss
- total_profit_loss_pct
- is_default
- created_at
- updated_at
```

### Positions Table
```sql
- id (PK)
- portfolio_id (FK)
- symbol
- quantity
- average_buy_price
- current_price
- total_invested
- current_value
- profit_loss
- profit_loss_pct
- last_updated
- created_at
```

### Trades Table
```sql
- id (PK)
- user_id (FK)
- portfolio_id (FK)
- symbol
- order_type (MARKET, LIMIT, STOP_LOSS)
- order_side (BUY, SELL)
- order_status (PENDING, EXECUTED, CANCELLED, REJECTED)
- quantity
- price
- limit_price
- stop_loss_price
- total_value
- commission
- notes
- executed_at
- created_at
```

### Watchlists Table
```sql
- id (PK)
- user_id (FK)
- symbol
- name
- sector
- added_price
- notes
- alert_price_high
- alert_price_low
- is_active
- created_at
```

---

## 🚀 Deployment Architecture

### Single Server Deployment

```
┌─────────────────────────────────────────┐
│           Your Domain                   │
│         (yourdomain.com)                │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTPS (443)
                  ▼
┌─────────────────────────────────────────┐
│             Nginx                       │
│  - SSL/TLS Termination                  │
│  - Reverse Proxy                        │
│  - Static File Serving                  │
│  - Load Balancing                       │
└─────────┬───────────────┬───────────────┘
          │               │
          │ /api/*        │ /static/*
          │               │
          ▼               ▼
┌─────────────────┐  ┌──────────────────┐
│  FastAPI        │  │  Frontend        │
│  (Backend)      │  │  (Static Files)  │
│  Port: 8000     │  │                  │
│  - REST API     │  │  - HTML          │
│  - Auth         │  │  - CSS           │
│  - Trading      │  │  - JavaScript    │
│  - Screening    │  │                  │
└────────┬────────┘  └──────────────────┘
         │
         │ Port: 5432
         ▼
┌─────────────────┐
│  PostgreSQL     │
│  (Database)     │
│  - User data    │
│  - Portfolios   │
│  - Trades       │
└─────────────────┘
```

---

## 📦 Dependencies

### Backend (Python)
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **SQLAlchemy**: ORM
- **PostgreSQL**: Database
- **pydantic**: Data validation
- **python-jose**: JWT handling
- **passlib**: Password hashing
- **authlib**: OAuth implementation
- **yfinance**: Stock data
- **pandas/numpy**: Data analysis
- **google-genai**: AI analysis

### Frontend
- **Vue.js 3**: Reactive framework
- **Axios**: HTTP client
- **Tailwind CSS**: Styling
- **Vanilla JavaScript**: Utilities

---

## 🔐 Security Features

1. **Authentication**
   - JWT tokens with expiration
   - Bcrypt password hashing
   - OAuth 2.0 with Google
   - Session management

2. **Authorization**
   - Protected API routes
   - User-specific data isolation
   - Role-based access (can be extended)

3. **Data Protection**
   - Environment variables for secrets
   - HTTPS/SSL encryption
   - Secure password requirements
   - SQL injection prevention (ORM)

4. **Frontend Security**
   - Token storage in localStorage
   - Automatic token expiration handling
   - XSS prevention
   - CORS configuration

---

## 🔄 Data Flow

### Authentication Flow
```
1. User → Login/Register → Backend
2. Backend → Validate → Generate JWT
3. Backend → Create/Update User → Database
4. Backend → Return Token → Frontend
5. Frontend → Store Token → LocalStorage
6. Frontend → Use Token in Headers → All API Calls
```

### Google OAuth Flow
```
1. User → Click "Google Login" → Frontend
2. Frontend → Redirect → Backend OAuth Endpoint
3. Backend → Redirect → Google OAuth
4. User → Authorize → Google
5. Google → Callback → Backend
6. Backend → Exchange Code → Google User Info
7. Backend → Create/Link User → Database
8. Backend → Generate JWT → Redirect Frontend
9. Frontend → Extract Token → Store & Redirect Dashboard
```

### Trading Flow
```
1. User → Place Order → Frontend
2. Frontend → POST /api/v2/trading/trade → Backend
3. Backend → Validate Order → Trading Engine
4. Trading Engine → Fetch Current Price → yfinance
5. Trading Engine → Calculate Value → Update Portfolio/Position
6. Trading Engine → Save Trade → Database
7. Backend → Return Success → Frontend
8. Frontend → Update UI → Show Confirmation
```

---

## 🛠️ Development Setup

### Local Development

1. **Backend**:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requiewments.txt
   python main.py
   ```

2. **Frontend**:
   ```bash
   cd frontend
   python -m http.server 8080
   # Or use Live Server in VS Code
   ```

3. **Database**:
   ```bash
   # Install PostgreSQL
   createdb stock_trading
   # Tables will be created automatically on first run
   ```

### Production Deployment
See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete guide.

---

## 📝 Configuration Files

### `.env` (Backend)
```env
DATABASE_URL=postgresql://...
SECRET_KEY=...
GEMINI_API_KEY=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=...
FRONTEND_URL=...
```

### `config.js` (Frontend)
```javascript
const API_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : window.location.origin;
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
- Manual testing with browser
- Can add Cypress/Playwright for E2E tests

---

## 📊 Monitoring & Logs

### Backend Logs
```bash
# Development
python main.py  # Logs to console

# Production (systemd)
sudo journalctl -u stock-platform -f
```

### Nginx Logs
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Logs
```bash
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

---

## 🔄 Future Enhancements

1. **Backend**
   - WebSocket for real-time updates
   - More OAuth providers (GitHub, Facebook)
   - Email notifications
   - Advanced analytics API
   - Backtesting engine

2. **Frontend**
   - Mobile app (React Native)
   - Advanced charting (TradingView)
   - Real-time portfolio updates
   - Social trading features
   - Dark mode

3. **Infrastructure**
   - Docker containerization
   - Kubernetes orchestration
   - CI/CD pipeline
   - Automated backups
   - Monitoring dashboard (Grafana)

---

## 📚 Documentation

- [README.md](backend/README.md) - Project overview and features
- [SETUP.md](backend/SETUP.md) - Initial setup guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [GOOGLE_OAUTH_SETUP.md](backend/GOOGLE_OAUTH_SETUP.md) - OAuth configuration
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - This file

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 📄 License

[Your License Here]

---

## 👥 Team

- **Developer**: Your Name
- **Support**: your.email@example.com

---

**Last Updated**: November 2024

