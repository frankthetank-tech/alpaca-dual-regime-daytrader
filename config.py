"""
Strategy #3: Dual-Regime Intraday Long/Short Day Trading Bot
Configuration & Environment Parameters
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. ALPACA CREDENTIALS & ENVIRONMENT
# ==========================================
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "PKPNBG2JCQHNYC436SIQAGF5WC")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "5L1NMQPYK9mQSojm91geZHytfsdbrMaSCp5r56AyKgWE")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "True").lower() in ("true", "1", "yes")

# Base URLs
PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_BASE_URL = "https://api.alpaca.markets"
BASE_URL = PAPER_BASE_URL if ALPACA_PAPER else LIVE_BASE_URL

# Alpaca Market Data Feed ("sip" for consolidated NBBO, "iex" as fallback)
DATA_FEED = os.getenv("ALPACA_DATA_FEED", "iex")

# ==========================================
# 2. STRATEGY SPECIFICATION & PARAMETERS
# ==========================================
# Pure day trading constraints
MAX_ALLOCATION_PCT = 1.0       # 100% of available account equity (0% leverage)
STOP_LOSS_PCT = 0.012          # 1.2% intrabar protective stop loss
TAKE_PROFIT_PCT = 0.035        # 3.5% intrabar profit target
MIN_ATR_PCT = 0.015            # 20-day ATR% >= 1.5%
MIN_RVOL_15 = 1.25             # First 15-minute RVOL >= 1.25x
MIN_GAP_PCT = 0.003            # Gap magnitude >= 0.3%

# Schedule timings (Eastern Time)
SCHEDULE_SCAN_TIME = "09:45"   # 09:45 AM EST: Evaluate Macro Shield & submit conditional stop orders
SCHEDULE_CUTOFF_TIME = "11:30" # 11:30 AM EST: Cancel unfilled entry stop orders
SCHEDULE_MOC_TIME = "15:55"    # 15:55 PM EST: Liquidate all open positions (MOC exit)

# ==========================================
# 3. TRADABLE UNIVERSE (131 ASSETS - ZERO LEVERAGED ETFS)
# ==========================================
# Liquid S&P 100 leaders and major sector ETFs (All 16 leveraged ETFs strictly excluded)
UNIVERSE = [
    # Mega-Cap Tech & Growth Leaders
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "ADBE", "CRM",
    "AMD", "INTC", "QCOM", "TXN", "AMAT", "MU", "NOW", "INTU", "NFLX", "PANW",
    # Financials & Banks
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "SPGI", "CB", "MMC", "PGR",
    # Healthcare & Pharma
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "PFE", "DHR", "BMY", "AMGN", "GILD",
    # Industrials, Defense & Aerospace
    "CAT", "GE", "HON", "UNP", "UPS", "BA", "LMT", "RTX", "DE", "ETN", "WM", "FDX",
    # Consumer & Retail
    "WMT", "COST", "HD", "PG", "KO", "PEP", "MCD", "NKE", "SBUX", "TGT", "LOW", "TJX",
    # Energy & Utilities
    "XOM", "CVX", "COP", "SLB", "EOG", "NEE", "SO", "DUK", "CEG",
    # Non-Leveraged Sector & Broad Benchmark ETFs
    "SPY", "QQQ", "IWM", "DIA", "SMH", "XLE", "XLF", "XLK", "XLV", "XLI", 
    "XLU", "XLP", "XLY", "XBI", "XME", "XRT", "XHB", "IYR", "IYT", "OIH"
]
