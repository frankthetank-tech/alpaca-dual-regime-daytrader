"""
Strategy #3: Dual-Regime Intraday Long/Short Day Trading Bot
Configuration & Environment Parameters (ORB-15 Cond 4 V2)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. ALPACA CREDENTIALS & ENVIRONMENT
# ==========================================
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_PAPER = os.getenv("ALPACA_PAPER", "True").lower() in ("true", "1", "yes")

# Base URLs
PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_BASE_URL = "https://api.alpaca.markets"
BASE_URL = PAPER_BASE_URL if ALPACA_PAPER else LIVE_BASE_URL

# Alpaca Market Data Feed ("sip" for consolidated NBBO, "iex" as fallback)
DATA_FEED = os.getenv("ALPACA_DATA_FEED", "iex")

# ==========================================
# 2. STRATEGY SPECIFICATION & PARAMETERS (Cond 4 V2)
# ==========================================
# Margin and Leverage Model
# Default: 100% Margin (2.0x Buying Power, Canadian CIRO / US Day Trading margin)
# Closed flat intraday before 16:00 PM close -> $0.00 overnight margin interest
MARGIN_PERCENT = float(os.getenv("MARGIN_PERCENT", "1.0"))  # 1.0 = 100% margin ($1 borrowed per $1 cash)
BUYING_POWER_MULT = 1.0 + MARGIN_PERCENT                   # 2.0x Intraday Buying Power

# Intraday Risk Management
STOP_LOSS_PCT = 0.012          # 1.2% fixed intrabar stop loss

# Dynamic ATR-Scaled Profit Target (Adjustment 1)
# Target = max(2.0%, min(4.5%, 1.5 * ATR%_20))
MIN_TARGET_PCT = 0.020         # 2.0% floor
MAX_TARGET_PCT = 0.045         # 4.5% ceiling
ATR_TARGET_MULT = 1.5          # 1.5x 20-day ATR%

def get_dynamic_target_pct(atr_pct: float) -> float:
    """Calculates dynamic profit target percentage scaled to 20-day ATR%."""
    return max(MIN_TARGET_PCT, min(MAX_TARGET_PCT, ATR_TARGET_MULT * atr_pct))

# Core Setup Filters
MIN_ATR_PCT = 0.015            # 20-day ATR% >= 1.5%
MIN_RVOL_15 = 1.25             # First 15-minute RVOL >= 1.25x
MIN_GAP_PCT = 0.003            # Minimum gap magnitude >= 0.3%
MAX_LONG_GAP = 0.045           # Gap-and-Trap Circuit Breaker: Max long gap <= 4.5%

# Multi-Order Execution & Throttling
ORDER_THROTTLE_RATE = 6.0      # 6 orders per second (0.167s interval between submissions)

def get_max_positions(cash_equity: float) -> int:
    """
    Dynamic Account Tier Allocation dictates maximum concurrent positions
    based on cash equity (preserves alpha concentration & prevents dilution).
    """
    if cash_equity < 15000.0:
        return 2     # Tier 1 ($5k - $15k): 2 positions max (50% max each)
    elif cash_equity < 50000.0:
        return 3     # Tier 2 ($15k - $50k): 3 positions max (33.3% max each)
    elif cash_equity < 150000.0:
        return 4     # Tier 3 ($50k - $150k): 4 positions max (25% max each)
    elif cash_equity < 500000.0:
        return 5     # Tier 4 ($150k - $500k): 5 positions max (20% max each)
    else:
        return 8     # Tier 5 ($500k+): 8 positions max (12.5% max each)

# Schedule timings (Eastern Time)
SCHEDULE_WARMUP_TIME = "09:25" # 09:25 AM EDT (13:25 UTC): Early Boot, 90-day pre-fetch (absorbs runner queue delays)
SCHEDULE_SCAN_TIME = "09:45:04" # 09:45:04 AM EDT: 4-second aggregation buffer to ensure 09:44 bar is published
SCHEDULE_CUTOFF_TIME = "11:30" # 11:30 AM EDT: Cancel unfilled resting entry stop orders
SCHEDULE_MOC_TIME = "15:45"    # 15:45 PM EDT: Early liquidation trigger (100% flat before 16:00 close)

# ==========================================
# 3. TRADABLE UNIVERSE & TOXIC BLACKLIST
# ==========================================
from universe_500 import UNIVERSE_500
from universe_institutional_v2 import TOXIC_BLACKLIST

# Dynamic Universe: All liquid universe assets excluding structurally toxic drag (banks, utilities, staples, commodity ETFs)
UNIVERSE = [s for s in UNIVERSE_500 if s not in TOXIC_BLACKLIST]
