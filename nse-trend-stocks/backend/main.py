"""
NSE Stock Screener - Enhanced Backend API
FastAPI server with comprehensive technical analysis and scoring
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import time
import requests
from google import genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress verbose yfinance logging
logging.getLogger('yfinance').setLevel(logging.ERROR)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
gemini_client = None

if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✓ Gemini AI configured successfully with google-genai")
    except Exception as e:
        logger.error(f"Failed to configure Gemini AI: {e}")
        gemini_client = None
else:
    logger.warning("⚠ GEMINI_API_KEY not found in environment variables. AI analysis will not be available.")

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced NSE Stock Screener API",
    version="2.0.0",
    description="Advanced stock screening with 120-point scoring system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# DATA MODELS
# =====================================================

class ScreeningFilters(BaseModel):
    strength_levels: Optional[List[str]] = None
    min_score: Optional[int] = 40
    max_score: Optional[int] = 120
    min_adx: Optional[int] = 20
    rsi_min: Optional[int] = 45
    rsi_max: Optional[int] = 80
    volume_surge_min: Optional[int] = 100
    breakout_type: Optional[str] = None
    market_cap: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

# =====================================================
# STOCK UNIVERSE
# =====================================================

# NIFTY 500 Stocks - Major companies from NSE
NIFTY_500_STOCKS = [
    # Top 50 - NIFTY 50
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK",
    "SBIN", "BHARTIARTL", "BAJFINANCE", "ASIANPAINT", "ITC", "AXISBANK", "LT",
    "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO",
    "TATAMOTORS", "ADANIENT", "ONGC", "NTPC", "POWERGRID", "M&M", "BAJAJFINSV",
    "COALINDIA", "TECHM", "INDUSINDBK", "TATASTEEL", "HDFCLIFE", "SBILIFE",
    "GRASIM", "DIVISLAB", "BRITANNIA", "BAJAJ-AUTO", "CIPLA", "DRREDDY", "EICHERMOT",
    "HINDALCO", "APOLLOHOSP", "VEDL", "JSWSTEEL", "HEROMOTOCO", "ADANIPORTS", "TATACONSUM",
    "HCLTECH", "DMART", "PIDILITIND",
    
    # NIFTY Next 50
    "ADANIGREEN", "ADANITRANS", "AMBUJACEM", "ATGL", "BANDHANBNK", "BERGEPAINT",
    "BOSCHLTD", "CHOLAFIN", "COLPAL", "DABUR", "DLF", "GODREJCP", "GAIL", "HAVELLS",
    "ICICIPRULI", "INDIGO", "JINDALSTEL", "LTIM", "MARICO", "MCDOWELL-N", "MUTHOOTFIN",
    "NAUKRI", "NMDC", "ICICIGI", "OFSS", "PGHH", "PIIND", "PNB", "SBICARD", "SHREECEM",
    "SIEMENS", "SRF", "TATAPOWER", "TORNTPHARM", "TRENT", "TVSMOTOR", "UBL", "UPL",
    "VOLTAS", "ZYDUSLIFE", "ABB", "ACC", "ALKEM", "ASTRAL", "AUBANK", "AUROPHARMA",
    "BALKRISIND", "BANKBARODA", "BEL",
    
    # NIFTY Midcap 100 (Selection)
    "AARTIIND", "ABBOTINDIA", "ABCAPITAL", "ABFRL", "APOLLOTYRE", "ASHOKLEY",
    "ASIANPAINT", "ASTERDM", "BAJAJHLDNG", "BATAINDIA", "BHARATFORG", "BIOCON",
    "BOSCHLTD", "BPCL", "CADILAHC", "CANBK", "CANFINHOME", "CHAMBLFERT", "COFORGE",
    "CONCOR", "COROMANDEL", "CROMPTON", "CUMMINSIND", "DEEPAKNTR", "DELTACORP",
    "DIXON", "DMART", "ESCORTS", "EXIDEIND", "FEDERALBNK", "GLENMARK", "GMRINFRA",
    "GNFC", "GODFRYPHLP", "GODREJPROP", "GRAPHITE", "GUJGASLTD", "HAL", "HINDCOPPER",
    "HINDPETRO", "HONAUT", "IBREALEST", "IDBI", "IDFCFIRSTB", "IEX", "IGL", "INDUSTOWER",
    "IOC", "IRCTC", "IRFC", "ISEC", "JINDALSAW", "JKCEMENT", "JUBLFOOD", "KAJARIACER",
    
    # NIFTY Midcap 100 (Continued)
    "KEI", "KPITTECH", "LAURUSLABS", "LICHSGFIN", "LICI", "LTTS", "LUPIN", "MANAPPURAM",
    "MAZDOCK", "MCX", "METROBRAND", "MFSL", "MGL", "MOTHERSON", "MPHASIS", "MRF",
    "NATCOPHARM", "NATIONALUM", "NAM-INDIA", "NAUKRI", "NAVINFLUOR", "NHPC", "OBEROIRLTY",
    "OIL", "PAGEIND", "PERSISTENT", "PETRONET", "PFC", "PHOENIXLTD", "POLYCAB",
    "POLYMED", "POWERGRID", "PVR", "RAIN", "RAJESHEXPO", "RAMCOCEM", "RBLBANK",
    "RECLTD", "RELAXO", "SAIL", "SBICARD", "SCHAEFFLER", "SHRIRAMCIT", "SONACOMS",
    
    # NIFTY Smallcap & Others
    "STAR", "SUNPHARMA", "SUNTV", "SUPREMEIND", "SWANENERGY", "TATACHEM", "TATACOMM",
    "TATAELXSI", "TATAMTRDVR", "TEAMLEASE", "THERMAX", "TIMKEN", "TORNTPOWER", "TTML",
    "UJJIVAN", "UNIONBANK", "UNITDSPR", "UCOBANK", "UJJIVANSFB", "VGUARD", "VINATIORGA",
    "VOLTAS", "WESTLIFE", "WHIRLPOOL", "YESBANK", "ZEEL", "ZENSARTECH", "ZOMATO",
    
    # Additional Top Banking & Finance
    "BAJAJCON", "CHOLAHLDNG", "EDELWEISS", "EQUITAS", "FINPIPE", "HDFC", "HDFCAMC",
    "HDFCBANK", "ICICIGI", "ICICIPRULI", "IIFL", "L&TFH", "M&MFIN", "MUTHOOTFIN",
    "PEL", "SHRIRAMFIN", "SRTRANSFIN",
    
    # IT & Technology
    "COFORGE", "CYIENT", "INFY", "KPITTECH", "LTI", "LTTS", "MINDTREE", "MPHASIS",
    "OFSS", "PERSISTENT", "ROUTE", "TCS", "TECHM", "WIPRO", "ZENSARTECH",
    
    # Pharma & Healthcare
    "AARTIDRUGS", "ABBOTINDIA", "ALEMBICLTD", "ALKEM", "AUROPHARMA", "BIOCON",
    "CADILAHC", "CIPLA", "DIVISLAB", "DRREDDY", "GLENMARK", "GRANULES", "IPCALAB",
    "JBCHEPHARM", "LAURUSLABS", "LUPIN", "MANKIND", "NATCOPHARM", "PFIZER", "SUNPHARMA",
    "TORNTPHARM", "ZYDUSLIFE",
    
    # Automobiles & Auto Components
    "APOLLOTYRE", "ASHOKLEY", "BAJAJ-AUTO", "BALKRISIND", "BHARATFORG", "BOSCHLTD",
    "CEAT", "EICHERMOT", "ESCORTS", "EXIDEIND", "HEROMOTOCO", "M&M", "MARUTI",
    "MOTHERSON", "MRF", "SONACOMS", "TATAMOTORS", "TATAMTRDVR", "TVSMOTOR",
    
    # FMCG & Consumer
    "ASIANPAINT", "BRITANNIA", "COLPAL", "DABUR", "EMAMILTD", "GODREJCP", "GODREJIND",
    "HINDUNILVR", "ITC", "JYOTHYLAB", "MARICO", "NESTLEIND", "TATACONSUM", "TITAN",
    "UBL", "VBL", "VENKEYS",
    
    # Infrastructure & Construction
    "ACC", "ADANIPORTS", "AMBUJACEM", "ASHOKA", "CESC", "DLF", "GAIL", "GMRINFRA",
    "HAL", "IPCL", "IRB", "IRCON", "JKCEMENT", "KNR", "L&T", "LINDEINDIA", "NBCC",
    "NCC", "NHPC", "NIACL", "NTPC", "OIL", "ONGC", "PFC", "PNB", "POWERGRID", "RECLTD",
    "SAIL", "SUNTECK", "TATAPOWER",
    
    # Metals & Mining
    "APLAPOLLO", "COALINDIA", "HINDALCO", "HINDCOPPER", "HINDZINC", "JINDALSTEL",
    "JSWSTEEL", "MOIL", "NATIONALUM", "NMDC", "RATNAMANI", "SAIL", "TATASTEEL",
    "VEDL", "WELCORP", "WELSPUNIND",
    
    # Oil & Gas
    "BPCL", "GAIL", "GSPL", "GUJGASLTD", "HINDPETRO", "IGL", "IOC", "MGL", "ONGC",
    "OIL", "PETRONET", "RELIANCE",
    
    # Telecom & Media
    "BHARTIARTL", "HATHWAY", "SUNTV", "TATACOMM", "TV18BRDCST", "ZEEL",
    
    # Retail & E-commerce
    "ABFRL", "ADITYANB", "BATA", "DMART", "JUBLFOOD", "SHOPERSTOP", "TRENT",
    "TITAN", "WESTLIFE", "ZOMATO",
    
    # Chemicals & Fertilizers
    "AARTI", "ATUL", "BALRAMCHIN", "CHAMBLFERT", "DEEPAKNTR", "FLUOROCHEM",
    "GNFC", "GUJALKALI", "NAVINFLUOR", "PIDILITIND", "SRF", "TATACHEM", "UPL",
    
    # Cement
    "ACC", "AMBUJACEM", "DALMIACEM", "HEIDELBERG", "JKCEMENT", "RAMCOCEM",
    "SHREECEM", "ULTRACEMCO",
    
    # Power & Energy
    "ADANIGREEN", "ADANIPOWER", "ADANITRANS", "CESC", "JSW ENERGY", "NHPC", "NTPC",
    "PFC", "POWERGRID", "RECLTD", "SJVN", "TATAPOWER", "TORNTPOWER"
]

SECTOR_MAPPING = {
    "RELIANCE": "Oil & Gas", "TCS": "IT", "HDFCBANK": "Banking", "INFY": "IT",
    "HINDUNILVR": "FMCG", "ICICIBANK": "Banking", "KOTAKBANK": "Banking",
    "SBIN": "Banking", "BHARTIARTL": "Telecom", "BAJFINANCE": "Financial Services",
    "ASIANPAINT": "Paints", "ITC": "FMCG", "AXISBANK": "Banking", "LT": "Infrastructure",
    "DMART": "Retail", "HCLTECH": "IT", "MARUTI": "Automobiles", "SUNPHARMA": "Pharmaceuticals",
    "TITAN": "Consumer Goods", "ULTRACEMCO": "Cement", "NESTLEIND": "FMCG",
    "WIPRO": "IT", "TATAMOTORS": "Automobiles", "ADANIENT": "Diversified",
    "ONGC": "Oil & Gas", "NTPC": "Power", "POWERGRID": "Power", "M&M": "Automobiles"
}

# =====================================================
# TECHNICAL INDICATORS ENGINE
# =====================================================

class TechnicalEngine:
    """Calculate all technical indicators"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.close = df['Close']
        self.high = df['High']
        self.low = df['Low']
        self.volume = df['Volume']
    
    def calculate_ema(self, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return self.close.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, period: int) -> pd.Series:
        """Simple Moving Average"""
        return self.close.rolling(window=period).mean()
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = self.close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_macd(self):
        """MACD Indicator"""
        ema12 = self.calculate_ema(12)
        ema26 = self.calculate_ema(26)
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        histogram = macd - signal
        return macd, signal, histogram
    
    def calculate_adx(self, period: int = 14):
        """Average Directional Index"""
        high_diff = self.high.diff()
        low_diff = -self.low.diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        tr1 = self.high - self.low
        tr2 = abs(self.high - self.close.shift())
        tr3 = abs(self.low - self.close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2):
        """Bollinger Bands"""
        middle = self.calculate_sma(period)
        std = self.close.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr1 = self.high - self.low
        tr2 = abs(self.high - self.close.shift())
        tr3 = abs(self.low - self.close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def calculate_obv(self) -> pd.Series:
        """On-Balance Volume"""
        obv = (np.sign(self.close.diff()) * self.volume).fillna(0).cumsum()
        return obv
    
    def calculate_roc(self, period: int = 10) -> pd.Series:
        """Rate of Change"""
        return ((self.close - self.close.shift(period)) / self.close.shift(period)) * 100
    
    def calculate_all_indicators(self) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        
        # Moving Averages
        self.df['EMA_20'] = self.calculate_ema(20)
        self.df['SMA_50'] = self.calculate_sma(50)
        self.df['SMA_200'] = self.calculate_sma(200)
        
        # Calculate slopes (percentage change over 5 days)
        self.df['EMA_20_slope'] = (self.df['EMA_20'].pct_change(5) * 100)
        self.df['SMA_50_slope'] = (self.df['SMA_50'].pct_change(5) * 100)
        self.df['SMA_200_slope'] = (self.df['SMA_200'].pct_change(5) * 100)
        
        # Oscillators
        self.df['RSI'] = self.calculate_rsi(14)
        self.df['ROC'] = self.calculate_roc(10)
        
        # MACD
        macd, signal, histogram = self.calculate_macd()
        self.df['MACD'] = macd
        self.df['MACD_Signal'] = signal
        self.df['MACD_Hist'] = histogram
        self.df['Hist_Momentum'] = histogram.diff(3)
        
        # ADX System
        adx, plus_di, minus_di = self.calculate_adx(14)
        self.df['ADX'] = adx
        self.df['Plus_DI'] = plus_di
        self.df['Minus_DI'] = minus_di
        self.df['DI_Spread'] = plus_di - minus_di
        self.df['ADX_Rising'] = adx.diff(3) > 0
        
        # Volume
        self.df['Vol_SMA_20'] = self.volume.rolling(20).mean()
        self.df['Vol_SMA_50'] = self.volume.rolling(50).mean()
        self.df['Vol_Ratio'] = (self.volume / self.df['Vol_SMA_20']) * 100
        
        # OBV
        self.df['OBV'] = self.calculate_obv()
        self.df['OBV_EMA'] = self.df['OBV'].ewm(span=20, adjust=False).mean()
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands()
        self.df['BB_Upper'] = bb_upper
        self.df['BB_Middle'] = bb_middle
        self.df['BB_Lower'] = bb_lower
        self.df['BB_Position'] = ((self.close - bb_lower) / (bb_upper - bb_lower)) * 100
        
        # ATR
        self.df['ATR'] = self.calculate_atr(14)
        self.df['ATR_Percent'] = (self.df['ATR'] / self.close) * 100
        
        # Breakout levels
        self.df['High_52W'] = self.high.rolling(252).max()
        self.df['High_4W'] = self.high.rolling(20).max()
        self.df['High_2W'] = self.high.rolling(10).max()
        
        return self.df

# =====================================================
# ENHANCED SCORING ENGINE
# =====================================================

class ScoringEngine:
    """120-point scoring system"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.scores = {}
        self.total = 0
    
    def score_trend_alignment(self) -> int:
        """A. TREND ALIGNMENT (25 points)"""
        score = 0
        
        try:
            current = self.df['Close'].iloc[-1]
            ema20 = self.df['EMA_20'].iloc[-1]
            sma50 = self.df['SMA_50'].iloc[-1]
            sma200 = self.df['SMA_200'].iloc[-1]
            
            # Price Position (12 points)
            if pd.notna(ema20) and pd.notna(sma50) and pd.notna(sma200):
                if current > ema20 > sma50 > sma200:
                    score += 12
                elif current > sma50 > sma200:
                    score += 10
                elif current > sma50:
                    score += 7
                elif current > sma50 * 0.97:
                    score += 4
            
            # MA Slopes (8 points)
            slopes = {
                'ema20': self.df['EMA_20_slope'].iloc[-1],
                'sma50': self.df['SMA_50_slope'].iloc[-1],
                'sma200': self.df['SMA_200_slope'].iloc[-1]
            }
            
            if all(pd.notna(s) and s > 2 for s in slopes.values()):
                score += 8
            elif slopes['ema20'] > 2 and slopes['sma50'] > 2:
                score += 6
            elif slopes['ema20'] > 2:
                score += 3
            
            # MA Divergence (5 points)
            if pd.notna(ema20) and pd.notna(sma50) and pd.notna(sma200):
                if ema20 > sma50 > sma200:
                    spacing = (ema20 - sma50) / sma50 * 100
                    if spacing > 2:
                        score += 5
                    elif spacing > 0:
                        score += 3
        
        except Exception as e:
            logger.error(f"Error in trend alignment scoring: {e}")
        
        self.scores['Trend Alignment'] = score
        return score
    
    def score_momentum_strength(self) -> int:
        """B. MOMENTUM & STRENGTH (35 points)"""
        score = 0
        
        try:
            # ADX (10 points)
            adx = self.df['ADX'].iloc[-1]
            if pd.notna(adx):
                if adx > 40:
                    score += 10
                elif adx > 30:
                    score += 8
                elif adx > 25:
                    score += 6
                elif adx > 20:
                    score += 4
            
            # DI Spread (5 points)
            di_spread = self.df['DI_Spread'].iloc[-1]
            adx_rising = self.df['ADX_Rising'].iloc[-1]
            if pd.notna(di_spread):
                if di_spread > 10 and adx_rising:
                    score += 5
                elif di_spread > 5:
                    score += 3
                elif di_spread > 0:
                    score += 1
            
            # RSI (8 points)
            rsi = self.df['RSI'].iloc[-1]
            if pd.notna(rsi):
                if 60 <= rsi <= 70:
                    score += 8
                elif 55 <= rsi <= 65:
                    score += 6
                elif 50 <= rsi <= 60:
                    score += 4
                elif 45 <= rsi <= 55:
                    score += 2
            
            # ROC (4 points)
            roc = self.df['ROC'].iloc[-1]
            if pd.notna(roc):
                if roc > 8:
                    score += 4
                elif roc > 4:
                    score += 3
                elif roc > 2:
                    score += 2
                elif roc > 0:
                    score += 1
            
            # MACD (8 points)
            macd = self.df['MACD'].iloc[-1]
            signal = self.df['MACD_Signal'].iloc[-1]
            hist = self.df['MACD_Hist'].iloc[-1]
            hist_mom = self.df['Hist_Momentum'].iloc[-1]
            
            if pd.notna(macd) and pd.notna(signal):
                if macd > signal and hist > 0 and hist_mom > 0:
                    score += 8
                elif macd > signal and hist > 0:
                    score += 6
                elif macd > signal:
                    score += 4
        
        except Exception as e:
            logger.error(f"Error in momentum scoring: {e}")
        
        self.scores['Momentum & Strength'] = score
        return score
    
    def score_volume_liquidity(self) -> int:
        """C. VOLUME & LIQUIDITY (20 points)"""
        score = 0
        
        try:
            # Volume Surge (8 points)
            vol_ratio = self.df['Vol_Ratio'].iloc[-1]
            if pd.notna(vol_ratio):
                if vol_ratio > 200:
                    score += 8
                elif vol_ratio > 150:
                    score += 6
                elif vol_ratio > 120:
                    score += 4
                elif vol_ratio > 100:
                    score += 2
            
            # OBV (6 points)
            obv = self.df['OBV'].iloc[-1]
            obv_ema = self.df['OBV_EMA'].iloc[-1]
            obv_high = self.df['OBV'].iloc[-50:].max()
            
            if pd.notna(obv) and pd.notna(obv_ema):
                if obv >= obv_high:
                    score += 6
                elif obv > obv_ema:
                    score += 4
                else:
                    score += 2
            
            # Volume-Price Confirmation (6 points)
            # Simplified: check if volume is trending with price
            vol_trend = self.df['Volume'].iloc[-10:].mean() / self.df['Volume'].iloc[-20:-10].mean()
            price_trend = self.df['Close'].iloc[-10:].mean() / self.df['Close'].iloc[-20:-10].mean()
            
            if vol_trend > 1 and price_trend > 1:
                score += 6
            elif vol_trend > 1 or price_trend > 1:
                score += 3
        
        except Exception as e:
            logger.error(f"Error in volume scoring: {e}")
        
        self.scores['Volume & Liquidity'] = score
        return score
    
    def score_price_action_breakouts(self) -> int:
        """D. PRICE ACTION & BREAKOUTS (25 points)"""
        score = 0
        
        try:
            current = self.df['Close'].iloc[-1]
            
            # Weekly Momentum (10 points) - simplified with daily data
            weekly_closes = self.df['Close'].iloc[-35::5]  # Sample every 5 days
            consecutive = 0
            for i in range(len(weekly_closes)-1, 0, -1):
                if weekly_closes.iloc[i] > weekly_closes.iloc[i-1]:
                    consecutive += 1
                else:
                    break
            
            if consecutive >= 5:
                score += 10
            elif consecutive >= 3:
                score += 7
            elif consecutive >= 2:
                score += 4
            elif consecutive >= 1:
                score += 2
            
            # Breakout Quality (8 points)
            high_52w = self.df['High_52W'].iloc[-2]
            high_4w = self.df['High_4W'].iloc[-2]
            high_2w = self.df['High_2W'].iloc[-2]
            vol_ratio = self.df['Vol_Ratio'].iloc[-1]
            
            if pd.notna(high_52w) and current >= high_52w * 0.995 and vol_ratio > 150:
                score += 8
            elif pd.notna(high_4w) and current >= high_4w * 0.995:
                score += 7
            elif pd.notna(high_2w) and current >= high_2w * 0.995:
                score += 5
            
            # Support/Resistance (7 points) - simplified
            lows = self.df['Low'].iloc[-20:]
            highs = self.df['High'].iloc[-20:]
            
            if len(lows) > 0 and len(highs) > 0:
                low_trend = np.polyfit(range(len(lows)), lows, 1)[0]
                if low_trend > 0:  # Ascending lows
                    score += 7
                else:
                    score += 3
        
        except Exception as e:
            logger.error(f"Error in price action scoring: {e}")
        
        self.scores['Price Action & Breakouts'] = score
        return score
    
    def score_volatility_risk(self) -> int:
        """E. VOLATILITY & RISK (10 points)"""
        score = 0
        
        try:
            # Bollinger Position (6 points)
            bb_position = self.df['BB_Position'].iloc[-1]
            if pd.notna(bb_position):
                if bb_position > 80:
                    score += 6
                elif bb_position > 60:
                    score += 4
                elif bb_position > 50:
                    score += 2
            
            # ATR (4 points)
            atr_current = self.df['ATR_Percent'].iloc[-1]
            atr_past = self.df['ATR_Percent'].iloc[-10]
            
            if pd.notna(atr_current) and pd.notna(atr_past):
                atr_change = ((atr_current - atr_past) / atr_past) * 100
                if 10 <= atr_change <= 20:
                    score += 4
                elif -5 <= atr_change <= 10:
                    score += 3
                elif -10 <= atr_change < -5:
                    score += 2
        
        except Exception as e:
            logger.error(f"Error in volatility scoring: {e}")
        
        self.scores['Volatility & Risk'] = score
        return score
    
    def score_ichimoku(self) -> int:
        """F. ICHIMOKU CLOUD (5 points) - Simplified"""
        score = 0
        
        try:
            # Simplified: use 9/26 period moving averages as proxy
            tenkan = self.df['Close'].rolling(9).mean().iloc[-1]
            kijun = self.df['Close'].rolling(26).mean().iloc[-1]
            current = self.df['Close'].iloc[-1]
            
            if pd.notna(tenkan) and pd.notna(kijun):
                if current > kijun and tenkan > kijun:
                    distance = ((current - kijun) / kijun) * 100
                    if distance > 10:
                        score += 5
                    elif distance > 5:
                        score += 4
                    else:
                        score += 2
        
        except Exception as e:
            logger.error(f"Error in ichimoku scoring: {e}")
        
        self.scores['Ichimoku Cloud'] = score
        return score
    
    def calculate_total_score(self) -> Dict[str, Any]:
        """Calculate total score and classification"""
        
        self.total = (
            self.score_trend_alignment() +
            self.score_momentum_strength() +
            self.score_volume_liquidity() +
            self.score_price_action_breakouts() +
            self.score_volatility_risk() +
            self.score_ichimoku()
        )
        
        # Classification
        if self.total >= 100:
            classification = "Exceptional"
            color = "#047857"
        elif self.total >= 85:
            classification = "Very High"
            color = "#065f46"
        elif self.total >= 70:
            classification = "High"
            color = "#059669"
        elif self.total >= 55:
            classification = "Medium"
            color = "#d97706"
        elif self.total >= 40:
            classification = "Low"
            color = "#dc2626"
        else:
            classification = "Weak"
            color = "#991b1b"
        
        return {
            'total_score': self.total,
            'classification': classification,
            'color': color,
            'category_scores': self.scores
        }

# =====================================================
# DATA FETCHING & CACHING
# =====================================================

# Simple in-memory cache
_cache = {}
_cache_timestamps = {}
CACHE_DURATION = 3600  # 1 hour

# Shared session for yfinance (helps with rate limiting)
_yf_session = requests.Session()
_yf_session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'})

def get_cached_data(key: str):
    """Get cached data if not expired"""
    if key in _cache:
        timestamp = _cache_timestamps.get(key, 0)
        if datetime.now().timestamp() - timestamp < CACHE_DURATION:
            return _cache[key]
    return None

def set_cached_data(key: str, data: Any):
    """Store data in cache"""
    _cache[key] = data
    _cache_timestamps[key] = datetime.now().timestamp()

def fetch_stocks_batch(symbols: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
    """
    Fetch multiple stocks at once using yf.download() - More efficient and less rate limiting
    """
    ticker_symbols = [f"{symbol}.NS" for symbol in symbols]
    ticker_string = " ".join(ticker_symbols)
    
    try:
        logger.info(f"Batch fetching {len(symbols)} stocks...")
        
        # Download all stocks at once
        data = yf.download(
            ticker_string,
            period=period,
            group_by='ticker',
            progress=False,
            threads=True
        )
        
        results = {}
        
        # If only one stock, data structure is different
        if len(symbols) == 1:
            if not data.empty and len(data) > 50:
                results[symbols[0]] = data
        else:
            # Multiple stocks - extract each one
            for symbol in symbols:
                ticker_symbol = f"{symbol}.NS"
                try:
                    if ticker_symbol in data.columns.levels[0]:
                        stock_data = data[ticker_symbol]
                        if not stock_data.empty and len(stock_data) > 50:
                            results[symbol] = stock_data
                            logger.debug(f"✓ Got {symbol} from batch")
                except Exception as e:
                    logger.debug(f"Could not extract {symbol} from batch: {e}")
        
        logger.info(f"Batch fetch successful: {len(results)}/{len(symbols)} stocks")
        return results
        
    except Exception as e:
        logger.warning(f"Batch fetch failed: {e}")
        return {}

def fetch_stock_data(symbol: str, period: str = "1y", max_retries: int = 2) -> pd.DataFrame:
    """
    Fetch stock data from yfinance with multiple fallback methods
    Tries: 1. yf.download() 2. ticker.history() 3. Shorter periods
    """
    
    ticker_symbol = f"{symbol}.NS"
    periods_to_try = [period, "6mo", "3mo"] if period == "1y" else [period]
    
    for period_attempt in periods_to_try:
        # Method 1: Use yf.download() - More reliable for batch operations
        try:
            logger.debug(f"Trying yf.download for {symbol} with period {period_attempt}")
            df = yf.download(
                ticker_symbol, 
                period=period_attempt,
                progress=False
            )
            
            if not df.empty and len(df) > 50:  # Need enough data for indicators
                logger.info(f"✓ Successfully fetched {symbol} using yf.download() with {period_attempt}")
                return df
            
        except Exception as e:
            logger.debug(f"yf.download failed for {symbol}: {str(e)[:100]}")
        
        # Method 2: Use ticker.history() with retries
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(2)
                
                logger.debug(f"Trying ticker.history for {symbol} (attempt {attempt + 1}/{max_retries})")
                ticker = yf.Ticker(ticker_symbol, session=_yf_session)
                
                # Try with different parameters
                df = ticker.history(
                    period=period_attempt,
                    interval="1d",
                    auto_adjust=True
                )
                
                if not df.empty and len(df) > 50:
                    logger.info(f"✓ Successfully fetched {symbol} using ticker.history() with {period_attempt}")
                    return df
                
            except Exception as e:
                logger.debug(f"ticker.history attempt {attempt + 1} failed for {symbol}: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        # If we've tried all methods with this period, try next shorter period
        if period_attempt != periods_to_try[-1]:
            logger.debug(f"Failed with {period_attempt} for {symbol}, trying shorter period...")
            time.sleep(0.5)
    
    # All methods failed
    error_msg = f"Unable to fetch data for {symbol} after trying all methods and periods"
    logger.error(error_msg)
    raise ValueError(error_msg)

def process_stock(symbol: str) -> Optional[Dict[str, Any]]:
    """Process a single stock and return scored results"""
    
    cache_key = f"stock:{symbol}"
    cached = get_cached_data(cache_key)
    if cached:
        return cached
    
    try:
        # Fetch data
        df = fetch_stock_data(symbol)
        
        # Calculate technical indicators
        tech_engine = TechnicalEngine(df)
        df_with_indicators = tech_engine.calculate_all_indicators()
        
        # Calculate score
        scoring = ScoringEngine(df_with_indicators)
        score_result = scoring.calculate_total_score()
        
        # Get latest values
        latest = df_with_indicators.iloc[-1]
        prev_close = df_with_indicators['Close'].iloc[-2]
        
        result = {
            'symbol': symbol,
            'name': symbol.replace('.NS', ''),
            'sector': SECTOR_MAPPING.get(symbol, 'Other'),
            'price': round(float(latest['Close']), 2),
            'change': round(float(latest['Close'] - prev_close), 2),
            'change_pct': round(((latest['Close'] - prev_close) / prev_close) * 100, 2),
            'volume': int(latest['Volume']),
            'total_score': score_result['total_score'],
            'classification': score_result['classification'],
            'color': score_result['color'],
            'category_scores': score_result['category_scores'],
            'indicators': {
                'rsi': round(float(latest['RSI']), 2) if pd.notna(latest['RSI']) else None,
                'adx': round(float(latest['ADX']), 2) if pd.notna(latest['ADX']) else None,
                'macd': round(float(latest['MACD']), 4) if pd.notna(latest['MACD']) else None,
                'volume_ratio': round(float(latest['Vol_Ratio']), 2) if pd.notna(latest['Vol_Ratio']) else None,
                'distance_50sma': round(((latest['Close'] - latest['SMA_50']) / latest['SMA_50']) * 100, 2) if pd.notna(latest['SMA_50']) else None,
                'distance_200sma': round(((latest['Close'] - latest['SMA_200']) / latest['SMA_200']) * 100, 2) if pd.notna(latest['SMA_200']) else None,
            },
            'signals': generate_trading_signals(df_with_indicators),
            'insights': generate_stock_insights(df_with_indicators, score_result, symbol),
            'trend_strength': calculate_trend_strength(df_with_indicators),
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache result
        set_cached_data(cache_key, result)
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing {symbol}: {e}")
        return None

# =====================================================
# HELPER FUNCTIONS FOR STOCK ANALYSIS
# =====================================================

def generate_trading_signals(df: pd.DataFrame) -> List[str]:
    """Generate trading signals from technical indicators"""
    signals = []
    
    try:
        latest = df.iloc[-1]
        
        # MACD Signal
        if pd.notna(latest['MACD']) and pd.notna(latest['MACD_Signal']):
            if latest['MACD'] > latest['MACD_Signal'] and latest['MACD_Hist'] > 0:
                signals.append("Bullish MACD crossover")
        
        # RSI Signal
        if pd.notna(latest['RSI']):
            if 60 <= latest['RSI'] <= 70:
                signals.append("RSI in strong momentum zone")
            elif latest['RSI'] > 80:
                signals.append("RSI overbought - potential pullback")
        
        # Trend Signal
        if pd.notna(latest['SMA_50']) and pd.notna(latest['SMA_200']):
            if latest['Close'] > latest['SMA_50'] > latest['SMA_200']:
                signals.append("Strong uptrend - all MAs aligned")
        
        # Volume Signal
        if pd.notna(latest['Vol_Ratio']) and latest['Vol_Ratio'] > 150:
            signals.append("High volume surge detected")
        
        # Breakout Signal
        if pd.notna(latest['High_52W']) and latest['Close'] >= latest['High_52W'] * 0.995:
            signals.append("Near 52-week high breakout")
            
    except Exception as e:
        logger.error(f"Error generating signals: {e}")
    
    return signals if signals else ["No strong signals detected"]


def generate_stock_insights(df: pd.DataFrame, score_result: Dict, symbol: str) -> List[str]:
    """Generate human-readable insights about the stock"""
    insights = []
    
    try:
        latest = df.iloc[-1]
        
        # Trend insight
        if score_result['category_scores'].get('Trend Alignment', 0) >= 20:
            insights.append(f"{symbol} is in a strong uptrend with well-aligned moving averages")
        elif score_result['category_scores'].get('Trend Alignment', 0) >= 15:
            insights.append(f"{symbol} shows positive trend alignment")
        
        # Momentum insight
        if pd.notna(latest['ADX']) and latest['ADX'] > 30:
            insights.append(f"Strong trend strength with ADX at {latest['ADX']:.1f}")
        
        # Volume insight
        if pd.notna(latest['Vol_Ratio']) and latest['Vol_Ratio'] > 150:
            insights.append(f"Exceptional volume activity at {latest['Vol_Ratio']:.0f}% of average")
        
        # Overall strength
        if score_result['total_score'] >= 85:
            insights.append("This stock demonstrates exceptional technical strength across all metrics")
        elif score_result['total_score'] >= 70:
            insights.append("Strong technical setup with multiple positive indicators")
            
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
    
    return insights if insights else ["Limited insights available"]


def calculate_trend_strength(df: pd.DataFrame) -> str:
    """Calculate overall trend strength"""
    try:
        latest = df.iloc[-1]
        
        # Check multiple factors
        factors = 0
        max_factors = 5
        
        # MA alignment
        if pd.notna(latest['EMA_20']) and pd.notna(latest['SMA_50']) and pd.notna(latest['SMA_200']):
            if latest['Close'] > latest['EMA_20'] > latest['SMA_50'] > latest['SMA_200']:
                factors += 2
            elif latest['Close'] > latest['SMA_50'] > latest['SMA_200']:
                factors += 1
        
        # ADX strength
        if pd.notna(latest['ADX']):
            if latest['ADX'] > 30:
                factors += 1
            elif latest['ADX'] > 25:
                factors += 0.5
        
        # RSI momentum
        if pd.notna(latest['RSI']) and 55 <= latest['RSI'] <= 75:
            factors += 1
        
        # Volume confirmation
        if pd.notna(latest['Vol_Ratio']) and latest['Vol_Ratio'] > 120:
            factors += 0.5
        
        # Classify
        strength_ratio = factors / max_factors
        if strength_ratio >= 0.8:
            return "Very Strong"
        elif strength_ratio >= 0.6:
            return "Strong"
        elif strength_ratio >= 0.4:
            return "Moderate"
        elif strength_ratio >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
            
    except Exception as e:
        logger.error(f"Error calculating trend strength: {e}")
        return "Unknown"


# =====================================================
# GEMINI AI ANALYSIS
# =====================================================

def analyze_stock_with_gemini(symbol: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use Gemini AI to provide comprehensive stock analysis"""
    
    if not gemini_client:
        return {
            "error": "Gemini API key not configured",
            "message": "Please set GEMINI_API_KEY environment variable to use AI analysis"
        }
    
    try:
        # Prepare the prompt with stock data
        prompt = f"""You are a professional stock analyst. Analyze the following NSE stock and provide detailed insights.

Stock Symbol: {symbol}
Current Price: ₹{stock_data['price']}
Price Change: {stock_data['change_pct']}%
Sector: {stock_data['sector']}

Technical Analysis Score: {stock_data['total_score']}/120
Classification: {stock_data['classification']}

Technical Indicators:
- RSI: {stock_data['indicators']['rsi']}
- ADX (Trend Strength): {stock_data['indicators']['adx']}
- MACD: {stock_data['indicators']['macd']}
- Volume Ratio: {stock_data['indicators']['volume_ratio']}%
- Distance from 50-day SMA: {stock_data['indicators']['distance_50sma']}%
- Distance from 200-day SMA: {stock_data['indicators']['distance_200sma']}%

Category Scores:
{', '.join([f"{k}: {v}" for k, v in stock_data['category_scores'].items()])}

Trend Strength: {stock_data.get('trend_strength', 'N/A')}

Current Signals: {', '.join(stock_data.get('signals', []))}

Please provide a comprehensive analysis covering:

1. **Uptrend Analysis**: Why is this stock in an uptrend? What technical factors are driving it?

2. **Technical Health**: Evaluate the technical strength. Are the indicators confirming the trend? Any divergences or warnings?

3. **Fundamental Perspective**: Based on the sector and general market knowledge, what fundamental factors might be supporting this trend? (Note: You can use general knowledge about the sector and major companies)

4. **Risk Assessment**: What are the potential risks? Any overbought conditions or warning signs?

5. **Trading Strategy**: 
   - Entry points and timing
   - Stop loss recommendations
   - Target levels
   - Holding period suggestion (short/medium/long term)

6. **Overall Recommendation**: Is this a good stock to invest in right now? Rate it on a scale of 1-10 and provide reasoning.

Please be specific, actionable, and balanced in your analysis. Format your response in clear sections."""

        # Use Gemini 2.5 Flash model with new API
        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt
        )
        
        return {
            "symbol": symbol,
            "analysis": response.text,
            "timestamp": datetime.now().isoformat(),
            "model": "gemini-2.0-flash-exp",
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error in Gemini analysis for {symbol}: {e}")
        return {
            "error": str(e),
            "message": "Failed to generate AI analysis",
            "status": "error"
        }


# =====================================================
# API ENDPOINTS
# =====================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Enhanced NSE Stock Screener API",
        "version": "2.0.0",
        "endpoints": {
            "screen": "/api/v2/stocks/screen",
            "stock_detail": "/api/v2/stock/{symbol}",
            "ai_analysis": "/api/v2/stock/{symbol}/analyze",
            "sectors": "/api/v2/sectors",
            "presets": "/api/v2/presets"
        },
        "features": {
            "technical_analysis": "120-point scoring system with comprehensive indicators",
            "ai_analysis": "Gemini AI-powered stock analysis with fundamental and technical insights"
        }
    }

@app.post("/api/v2/stocks/screen")
async def screen_stocks(filters: ScreeningFilters, background_tasks: BackgroundTasks):
    """Main screening endpoint with batch fetching"""
    
    try:
        start_time = datetime.now()
        
        # Get stock universe - NIFTY 500 (you can adjust the number)
        # Start with 100 stocks for reasonable performance, increase if needed
        num_stocks = 100  # Change this to len(NIFTY_500_STOCKS) to scan all 500
        symbols = list(set(NIFTY_500_STOCKS[:num_stocks]))  # Remove duplicates
        
        logger.info("=" * 60)
        logger.info(f"SCANNING {len(symbols)} STOCKS FROM NIFTY 500")
        logger.info(f"First 10: {', '.join(symbols[:10])}")
        logger.info("=" * 60)
        
        # Check cache first
        cached_symbols = []
        uncached_symbols = []
        results = []
        
        for symbol in symbols:
            cache_key = f"stock:{symbol}"
            cached = get_cached_data(cache_key)
            if cached:
                results.append(cached)
                cached_symbols.append(symbol)
            else:
                uncached_symbols.append(symbol)
        
        logger.info(f"Using {len(cached_symbols)} cached stocks, fetching {len(uncached_symbols)} new")
        
        # Batch fetch uncached stocks (more efficient, less rate limiting)
        if uncached_symbols:
            # Try batch fetch first
            batch_data = fetch_stocks_batch(uncached_symbols, period="1y")
            
            # Process successfully fetched stocks
            for symbol, df in batch_data.items():
                try:
                    # Calculate technical indicators
                    tech_engine = TechnicalEngine(df)
                    df_with_indicators = tech_engine.calculate_all_indicators()
                    
                    # Calculate score
                    scoring = ScoringEngine(df_with_indicators)
                    score_result = scoring.calculate_total_score()
                    
                    # Get latest values
                    latest = df_with_indicators.iloc[-1]
                    prev_close = df_with_indicators['Close'].iloc[-2]
                    
                    result = {
                        'symbol': symbol,
                        'name': symbol.replace('.NS', ''),
                        'sector': SECTOR_MAPPING.get(symbol, 'Other'),
                        'price': round(float(latest['Close']), 2),
                        'change': round(float(latest['Close'] - prev_close), 2),
                        'change_pct': round(((latest['Close'] - prev_close) / prev_close) * 100, 2),
                        'volume': int(latest['Volume']),
                        'total_score': score_result['total_score'],
                        'classification': score_result['classification'],
                        'color': score_result['color'],
                        'category_scores': score_result['category_scores'],
                        'indicators': {
                            'rsi': round(float(latest['RSI']), 2) if pd.notna(latest['RSI']) else None,
                            'adx': round(float(latest['ADX']), 2) if pd.notna(latest['ADX']) else None,
                            'macd': round(float(latest['MACD']), 4) if pd.notna(latest['MACD']) else None,
                            'volume_ratio': round(float(latest['Vol_Ratio']), 2) if pd.notna(latest['Vol_Ratio']) else None,
                            'distance_50sma': round(((latest['Close'] - latest['SMA_50']) / latest['SMA_50']) * 100, 2) if pd.notna(latest['SMA_50']) else None,
                            'distance_200sma': round(((latest['Close'] - latest['SMA_200']) / latest['SMA_200']) * 100, 2) if pd.notna(latest['SMA_200']) else None,
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Cache result
                    set_cached_data(f"stock:{symbol}", result)
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol} from batch: {e}")
            
            # For stocks that failed in batch, try individual fetch
            failed_symbols = set(uncached_symbols) - set(batch_data.keys())
            if failed_symbols:
                logger.info(f"Retrying {len(failed_symbols)} failed stocks individually...")
                for symbol in failed_symbols:
                    try:
                        result = process_stock(symbol)
                        if result:
                            results.append(result)
                        time.sleep(0.5)  # Small delay between individual fetches
                    except Exception as e:
                        logger.warning(f"Failed to fetch {symbol} individually: {e}")
        
        # Apply filters
        filtered_results = results
        
        # Filter by score
        if filters.min_score:
            filtered_results = [r for r in filtered_results if r['total_score'] >= filters.min_score]
        if filters.max_score:
            filtered_results = [r for r in filtered_results if r['total_score'] <= filters.max_score]
        
        # Filter by strength levels
        if filters.strength_levels:
            filtered_results = [r for r in filtered_results if r['classification'] in filters.strength_levels]
        
        # Filter by indicators
        if filters.min_adx:
            filtered_results = [r for r in filtered_results 
                              if r['indicators']['adx'] and r['indicators']['adx'] >= filters.min_adx]
        
        if filters.rsi_min or filters.rsi_max:
            rsi_min = filters.rsi_min or 0
            rsi_max = filters.rsi_max or 100
            filtered_results = [r for r in filtered_results 
                              if r['indicators']['rsi'] and rsi_min <= r['indicators']['rsi'] <= rsi_max]
        
        # Filter by sector
        if filters.sectors:
            filtered_results = [r for r in filtered_results if r['sector'] in filters.sectors]
        
        # Filter by price
        if filters.min_price:
            filtered_results = [r for r in filtered_results if r['price'] >= filters.min_price]
        if filters.max_price:
            filtered_results = [r for r in filtered_results if r['price'] <= filters.max_price]
        
        # Sort by score (descending)
        filtered_results.sort(key=lambda x: x['total_score'], reverse=True)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "total_screened": len(symbols),
            "total_matched": len(filtered_results),
            "execution_time": round(execution_time, 2),
            "results": filtered_results
        }
    
    except Exception as e:
        logger.error(f"Error in screening: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/stock/{symbol}")
async def get_stock_details(symbol: str):
    """Get detailed analysis for a specific stock"""
    
    try:
        result = process_stock(symbol)
        if not result:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        return result
    
    except Exception as e:
        logger.error(f"Error getting stock details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/stock/{symbol}/analyze")
async def analyze_stock_ai(symbol: str):
    """
    Get AI-powered analysis for a stock using Google's Gemini
    
    This endpoint provides comprehensive analysis including:
    - Why the stock is in an uptrend
    - Technical analysis evaluation
    - Fundamental perspective
    - Risk assessment
    - Trading strategy recommendations
    - Investment rating
    """
    
    try:
        # First get the stock data and technical analysis
        logger.info(f"Fetching stock data for AI analysis: {symbol}")
        stock_data = process_stock(symbol)
        
        if not stock_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Stock {symbol} not found or unable to fetch data"
            )
        
        # Get AI analysis from Gemini
        logger.info(f"Requesting Gemini AI analysis for {symbol}")
        ai_analysis = analyze_stock_with_gemini(symbol, stock_data)
        
        # Check if AI analysis was successful
        if ai_analysis.get('status') == 'error':
            return {
                "stock_data": stock_data,
                "ai_analysis": None,
                "error": ai_analysis.get('error'),
                "message": ai_analysis.get('message')
            }
        
        # Return combined data
        return {
            "stock_data": stock_data,
            "ai_analysis": ai_analysis,
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI stock analysis for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/sectors")
async def get_sectors():
    """Get list of available sectors"""
    sectors = list(set(SECTOR_MAPPING.values()))
    return {"sectors": sorted(sectors)}

@app.get("/api/v2/presets")
async def get_presets():
    """Get preset screening strategies"""
    return {
        "presets": {
            "strong_momentum": {
                "name": "Strong Momentum",
                "description": "Stocks with strong upward momentum and high trend strength",
                "filters": {
                    "min_adx": 30,
                    "rsi_min": 60,
                    "rsi_max": 75,
                    "volume_surge_min": 150,
                    "min_score": 80
                }
            },
            "fresh_breakouts": {
                "name": "Fresh Breakouts",
                "description": "Stocks breaking out to new highs with strong volume",
                "filters": {
                    "breakout_type": "52_week",
                    "volume_surge_min": 150,
                    "min_score": 75
                }
            },
            "smart_recovery": {
                "name": "Smart Recovery",
                "description": "Stocks showing recovery signs with bullish divergence",
                "filters": {
                    "rsi_min": 45,
                    "rsi_max": 60,
                    "min_score": 65
                }
            },
            "high_quality": {
                "name": "High Quality Trends",
                "description": "Stocks with strong overall technical health",
                "filters": {
                    "min_score": 85
                }
            }
        }
    }

@app.get("/api/v2/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(_cache)
    }

@app.get("/api/v2/test-fetch/{symbol}")
async def test_fetch(symbol: str):
    """Test endpoint to check if data fetching works for a specific stock"""
    try:
        logger.info(f"Testing fetch for {symbol}")
        df = fetch_stock_data(symbol, period="3mo")
        
        return {
            "status": "success",
            "symbol": symbol,
            "data_points": len(df),
            "date_range": {
                "start": str(df.index[0]),
                "end": str(df.index[-1])
            },
            "latest_close": float(df['Close'].iloc[-1]),
            "message": "Data fetched successfully"
        }
    except Exception as e:
        logger.error(f"Test fetch failed for {symbol}: {e}")
        return {
            "status": "error",
            "symbol": symbol,
            "error": str(e),
            "message": "Failed to fetch data. Check if yfinance is up to date: pip install --upgrade yfinance"
        }

if __name__ == "__main__":
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("NSE Stock Screener API - Starting Up")
    logger.info("=" * 60)
    logger.info("Testing yfinance connectivity...")
    
    # Quick test to verify yfinance is working
    try:
        test_ticker = yf.Ticker("RELIANCE.NS")
        test_data = test_ticker.history(period="5d")
        if not test_data.empty:
            logger.info(f"✓ yfinance working - Got {len(test_data)} days of RELIANCE data")
        else:
            logger.warning("⚠ yfinance returned empty data - API might be rate limited")
            logger.warning("  Try: pip install --upgrade yfinance")
    except Exception as e:
        logger.error(f"✗ yfinance test failed: {e}")
        logger.error("  Run: pip install --upgrade yfinance")
    
    logger.info("=" * 60)
    logger.info("Starting server on http://0.0.0.0:8000")
    logger.info("API docs at http://0.0.0.0:8000/docs")
    logger.info("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)