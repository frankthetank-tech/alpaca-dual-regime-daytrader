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

# Multi-Order Execution & Throttling
MAX_POSITIONS = 50             # Cap at maximum 50 qualified positions
ORDER_THROTTLE_RATE = 6.0      # 6 orders per second (0.167s interval between submissions)
ORDER_QTY = 1                  # Strictly 1 full whole share per order

# Schedule timings (Eastern Time)
SCHEDULE_WARMUP_TIME = "09:40" # 09:40 AM EST: Boot runner & pre-fetch 90-day daily metrics
SCHEDULE_SCAN_TIME = "09:45"   # 09:45 AM EST: Evaluate Macro Shield & submit conditional stop orders
SCHEDULE_CUTOFF_TIME = "11:30" # 11:30 AM EST: Cancel unfilled entry stop orders
SCHEDULE_MOC_TIME = "15:55"    # 15:55 PM EST: Liquidate all open positions (MOC exit)

# ==========================================
# 3. TRADABLE UNIVERSE (500 PREDEFINED ASSETS - ZERO LEVERAGED ETFS)
# ==========================================
from universe_500 import UNIVERSE_500

# Ultra-diversified 500-ticker universe (116 liquid ETFs + 384 GICS equities)
UNIVERSE = UNIVERSE_500
