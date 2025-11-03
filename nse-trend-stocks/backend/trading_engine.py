"""
Paper Trading Engine - Handles order execution, portfolio management, and P&L calculations
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Tuple
import yfinance as yf
import logging

from models import (
    User, Portfolio, Trade, Position, OrderType, OrderSide, OrderStatus
)
from schemas import TradeCreate

logger = logging.getLogger(__name__)


class TradingEngine:
    """Paper trading engine for executing trades and managing portfolios"""
    
    def __init__(self, db: Session):
        self.db = db
        self.commission_rate = 0.001  # 0.1% commission
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Fetch current price for a symbol from yfinance
        
        Args:
            symbol: Stock symbol (e.g., RELIANCE)
            
        Returns:
            Current price or None if failed
        """
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            data = ticker.history(period="1d")
            
            if data.empty:
                logger.error(f"No price data found for {symbol}")
                return None
            
            current_price = float(data['Close'].iloc[-1])
            return current_price
            
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return None
    
    def calculate_commission(self, total_value: float) -> float:
        """Calculate trading commission"""
        return total_value * self.commission_rate
    
    def execute_buy_order(
        self,
        user: User,
        portfolio: Portfolio,
        trade_data: TradeCreate
    ) -> Tuple[bool, str, Optional[Trade], Optional[Position]]:
        """
        Execute a BUY order
        
        Returns:
            (success, message, trade, position)
        """
        # Get current price
        current_price = self.get_current_price(trade_data.symbol)
        
        if current_price is None:
            return False, f"Could not fetch price for {trade_data.symbol}", None, None
        
        # For market orders, use current price
        execution_price = current_price
        
        # For limit orders, check if limit price is met
        if trade_data.order_type == OrderType.LIMIT:
            if trade_data.limit_price is None:
                return False, "Limit price is required for LIMIT orders", None, None
            
            if current_price > trade_data.limit_price:
                return False, f"Current price ₹{current_price:.2f} is above your limit price ₹{trade_data.limit_price:.2f}", None, None
            
            execution_price = trade_data.limit_price
        
        # Calculate total cost
        total_value = execution_price * trade_data.quantity
        commission = self.calculate_commission(total_value)
        total_cost = total_value + commission
        
        # Check if sufficient funds
        if portfolio.cash_balance < total_cost:
            return False, f"Insufficient funds. Required: ₹{total_cost:.2f}, Available: ₹{portfolio.cash_balance:.2f}", None, None
        
        # Create trade record
        trade = Trade(
            user_id=user.id,
            portfolio_id=portfolio.id,
            symbol=trade_data.symbol,
            order_type=trade_data.order_type,
            order_side=OrderSide.BUY,
            order_status=OrderStatus.EXECUTED,
            quantity=trade_data.quantity,
            price=execution_price,
            limit_price=trade_data.limit_price,
            stop_loss_price=trade_data.stop_loss_price,
            total_value=total_value,
            commission=commission,
            notes=trade_data.notes,
            executed_at=datetime.utcnow()
        )
        
        self.db.add(trade)
        
        # Update portfolio cash balance
        portfolio.cash_balance -= total_cost
        portfolio.total_invested += total_value
        
        # Update or create position
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.symbol == trade_data.symbol
        ).first()
        
        if position:
            # Update existing position
            total_quantity = position.quantity + trade_data.quantity
            total_cost = (position.average_buy_price * position.quantity) + total_value
            position.average_buy_price = total_cost / total_quantity
            position.quantity = total_quantity
            position.current_price = current_price
            position.total_invested = position.average_buy_price * position.quantity
            position.current_value = current_price * position.quantity
            position.profit_loss = position.current_value - position.total_invested
            position.profit_loss_pct = (position.profit_loss / position.total_invested) * 100 if position.total_invested > 0 else 0
            position.last_updated = datetime.utcnow()
        else:
            # Create new position
            position = Position(
                portfolio_id=portfolio.id,
                symbol=trade_data.symbol,
                quantity=trade_data.quantity,
                average_buy_price=execution_price,
                current_price=current_price,
                total_invested=total_value,
                current_value=current_price * trade_data.quantity,
                profit_loss=0.0,
                profit_loss_pct=0.0
            )
            self.db.add(position)
        
        # Commit transaction
        self.db.commit()
        self.db.refresh(trade)
        self.db.refresh(position)
        self.db.refresh(portfolio)
        
        return True, f"Successfully bought {trade_data.quantity} shares of {trade_data.symbol} at ₹{execution_price:.2f}", trade, position
    
    def execute_sell_order(
        self,
        user: User,
        portfolio: Portfolio,
        trade_data: TradeCreate
    ) -> Tuple[bool, str, Optional[Trade], Optional[Position]]:
        """
        Execute a SELL order
        
        Returns:
            (success, message, trade, position)
        """
        # Check if position exists
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.id,
            Position.symbol == trade_data.symbol
        ).first()
        
        if not position:
            return False, f"You don't own any shares of {trade_data.symbol}", None, None
        
        if position.quantity < trade_data.quantity:
            return False, f"Insufficient shares. You have {position.quantity}, trying to sell {trade_data.quantity}", None, None
        
        # Get current price
        current_price = self.get_current_price(trade_data.symbol)
        
        if current_price is None:
            return False, f"Could not fetch price for {trade_data.symbol}", None, None
        
        # For market orders, use current price
        execution_price = current_price
        
        # For limit orders, check if limit price is met
        if trade_data.order_type == OrderType.LIMIT:
            if trade_data.limit_price is None:
                return False, "Limit price is required for LIMIT orders", None, None
            
            if current_price < trade_data.limit_price:
                return False, f"Current price ₹{current_price:.2f} is below your limit price ₹{trade_data.limit_price:.2f}", None, None
            
            execution_price = trade_data.limit_price
        
        # Calculate proceeds
        total_value = execution_price * trade_data.quantity
        commission = self.calculate_commission(total_value)
        net_proceeds = total_value - commission
        
        # Create trade record
        trade = Trade(
            user_id=user.id,
            portfolio_id=portfolio.id,
            symbol=trade_data.symbol,
            order_type=trade_data.order_type,
            order_side=OrderSide.SELL,
            order_status=OrderStatus.EXECUTED,
            quantity=trade_data.quantity,
            price=execution_price,
            limit_price=trade_data.limit_price,
            stop_loss_price=trade_data.stop_loss_price,
            total_value=total_value,
            commission=commission,
            notes=trade_data.notes,
            executed_at=datetime.utcnow()
        )
        
        self.db.add(trade)
        
        # Calculate P&L for this trade
        cost_basis = position.average_buy_price * trade_data.quantity
        trade_pnl = total_value - cost_basis
        
        # Update portfolio
        portfolio.cash_balance += net_proceeds
        portfolio.total_invested -= cost_basis
        portfolio.total_profit_loss += trade_pnl
        
        # Update position
        position.quantity -= trade_data.quantity
        
        if position.quantity == 0:
            # Remove position if fully sold
            self.db.delete(position)
            position = None
        else:
            # Update remaining position
            position.current_price = current_price
            position.total_invested = position.average_buy_price * position.quantity
            position.current_value = current_price * position.quantity
            position.profit_loss = position.current_value - position.total_invested
            position.profit_loss_pct = (position.profit_loss / position.total_invested) * 100 if position.total_invested > 0 else 0
            position.last_updated = datetime.utcnow()
        
        # Update portfolio P&L percentage
        if portfolio.initial_balance > 0:
            portfolio.total_profit_loss_pct = (portfolio.total_profit_loss / portfolio.initial_balance) * 100
        
        # Commit transaction
        self.db.commit()
        self.db.refresh(trade)
        if position:
            self.db.refresh(position)
        self.db.refresh(portfolio)
        
        return True, f"Successfully sold {trade_data.quantity} shares of {trade_data.symbol} at ₹{execution_price:.2f}. P&L: ₹{trade_pnl:.2f}", trade, position
    
    def update_portfolio_values(self, portfolio: Portfolio):
        """
        Update all position values with current prices
        """
        positions = self.db.query(Position).filter(
            Position.portfolio_id == portfolio.id
        ).all()
        
        total_pnl = 0.0
        
        for position in positions:
            current_price = self.get_current_price(position.symbol)
            
            if current_price:
                position.current_price = current_price
                position.current_value = current_price * position.quantity
                position.profit_loss = position.current_value - position.total_invested
                position.profit_loss_pct = (position.profit_loss / position.total_invested) * 100 if position.total_invested > 0 else 0
                position.last_updated = datetime.utcnow()
                
                total_pnl += position.profit_loss
        
        # Update portfolio total P&L
        portfolio.total_profit_loss = total_pnl
        
        if portfolio.initial_balance > 0:
            portfolio.total_profit_loss_pct = (total_pnl / portfolio.initial_balance) * 100
        
        portfolio.updated_at = datetime.utcnow()
        
        self.db.commit()

