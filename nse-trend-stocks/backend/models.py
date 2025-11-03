"""
Database models for the stock trading platform
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base


class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Made optional for OAuth users
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # OAuth fields
    oauth_provider = Column(String, nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String, unique=True, nullable=True, index=True)  # Provider's user ID
    profile_picture = Column(String, nullable=True)  # User's profile picture URL
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")


class Portfolio(Base):
    """Portfolio model - tracks user's holdings and cash balance"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="Default Portfolio")
    cash_balance = Column(Float, default=1000000.0)  # Starting with 10 lakhs
    initial_balance = Column(Float, default=1000000.0)
    total_invested = Column(Float, default=0.0)
    total_profit_loss = Column(Float, default=0.0)
    total_profit_loss_pct = Column(Float, default=0.0)
    is_default = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")


class OrderType(str, enum.Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"


class OrderSide(str, enum.Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Trade(Base):
    """Trade model - records all buy/sell transactions"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    order_type = Column(SQLEnum(OrderType), default=OrderType.MARKET)
    order_side = Column(SQLEnum(OrderSide), nullable=False)
    order_status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Execution price
    limit_price = Column(Float)  # For limit orders
    stop_loss_price = Column(Float)  # For stop loss orders
    total_value = Column(Float, nullable=False)  # quantity * price
    commission = Column(Float, default=0.0)  # Trading fees
    notes = Column(Text)
    executed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="trades")
    portfolio = relationship("Portfolio", back_populates="trades")


class Position(Base):
    """Position model - current holdings in a portfolio"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    average_buy_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    total_invested = Column(Float, nullable=False)  # avg_price * quantity
    current_value = Column(Float, nullable=False)  # current_price * quantity
    profit_loss = Column(Float, default=0.0)  # current_value - total_invested
    profit_loss_pct = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")


class Watchlist(Base):
    """Watchlist model - user's stock watchlist"""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    name = Column(String)  # Stock name
    sector = Column(String)
    added_price = Column(Float)  # Price when added to watchlist
    notes = Column(Text)
    alert_price_high = Column(Float)  # Alert when price goes above
    alert_price_low = Column(Float)  # Alert when price goes below
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlists")


class PortfolioSnapshot(Base):
    """Historical snapshots of portfolio value - for performance tracking"""
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    total_value = Column(Float, nullable=False)  # cash + holdings value
    cash_balance = Column(Float, nullable=False)
    holdings_value = Column(Float, nullable=False)
    profit_loss = Column(Float, nullable=False)
    profit_loss_pct = Column(Float, nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow, index=True)

    # Store positions as JSON for historical record
    positions_snapshot = Column(JSON)

