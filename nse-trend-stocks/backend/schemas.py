"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import OrderType, OrderSide, OrderStatus


# =====================================================
# USER SCHEMAS
# =====================================================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str  # Can be username or email
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    is_verified: bool
    oauth_provider: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None


class GoogleAuthResponse(BaseModel):
    """Response after Google OAuth authentication"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =====================================================
# PORTFOLIO SCHEMAS
# =====================================================

class PortfolioBase(BaseModel):
    """Base portfolio schema"""
    name: str = "Default Portfolio"
    cash_balance: float = 1000000.0


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio"""
    initial_balance: float = 1000000.0


class PortfolioResponse(PortfolioBase):
    """Schema for portfolio response"""
    id: int
    user_id: int
    initial_balance: float
    total_invested: float
    total_profit_loss: float
    total_profit_loss_pct: float
    is_default: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =====================================================
# POSITION SCHEMAS
# =====================================================

class PositionResponse(BaseModel):
    """Schema for position response"""
    id: int
    portfolio_id: int
    symbol: str
    quantity: int
    average_buy_price: float
    current_price: float
    total_invested: float
    current_value: float
    profit_loss: float
    profit_loss_pct: float
    last_updated: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =====================================================
# TRADE SCHEMAS
# =====================================================

class TradeCreate(BaseModel):
    """Schema for creating a new trade"""
    symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE)")
    order_type: OrderType = OrderType.MARKET
    order_side: OrderSide
    quantity: int = Field(..., gt=0, description="Number of shares")
    limit_price: Optional[float] = Field(None, description="Price for limit orders")
    stop_loss_price: Optional[float] = Field(None, description="Price for stop loss orders")
    notes: Optional[str] = None


class TradeResponse(BaseModel):
    """Schema for trade response"""
    id: int
    user_id: int
    portfolio_id: int
    symbol: str
    order_type: OrderType
    order_side: OrderSide
    order_status: OrderStatus
    quantity: int
    price: float
    limit_price: Optional[float]
    stop_loss_price: Optional[float]
    total_value: float
    commission: float
    notes: Optional[str]
    executed_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TradeExecutionResponse(BaseModel):
    """Schema for trade execution response"""
    success: bool
    message: str
    trade: Optional[TradeResponse] = None
    portfolio: Optional[PortfolioResponse] = None
    position: Optional[PositionResponse] = None


# =====================================================
# WATCHLIST SCHEMAS
# =====================================================

class WatchlistCreate(BaseModel):
    """Schema for creating a watchlist item"""
    symbol: str
    name: Optional[str] = None
    sector: Optional[str] = None
    notes: Optional[str] = None
    alert_price_high: Optional[float] = None
    alert_price_low: Optional[float] = None


class WatchlistResponse(BaseModel):
    """Schema for watchlist response"""
    id: int
    user_id: int
    symbol: str
    name: Optional[str]
    sector: Optional[str]
    added_price: Optional[float]
    notes: Optional[str]
    alert_price_high: Optional[float]
    alert_price_low: Optional[float]
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# =====================================================
# PORTFOLIO SUMMARY SCHEMAS
# =====================================================

class PortfolioSummary(BaseModel):
    """Complete portfolio summary with positions"""
    portfolio: PortfolioResponse
    positions: List[PositionResponse]
    total_portfolio_value: float
    total_holdings_value: float
    cash_balance: float
    total_profit_loss: float
    total_profit_loss_pct: float
    num_positions: int


class DashboardSummary(BaseModel):
    """Complete dashboard summary for user"""
    user: UserResponse
    portfolio: PortfolioSummary
    recent_trades: List[TradeResponse]
    watchlist: List[WatchlistResponse]
    top_gainers: List[PositionResponse]
    top_losers: List[PositionResponse]

