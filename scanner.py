"""
Strategy #3: Scanner & Signal Engine
Evaluates 09:45 AM Dual-Regime Macro Shield and Ranks Long Leaders / Short Laggards
Equipped with Automatic Feed Failover (IEX / SIP) to Prevent 403 Forbidden Errors
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

import config
import state_manager

logger = logging.getLogger("DualRegime.Scanner")

def get_data_client():
    return StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)

def get_stock_bars_safe(client, symbol_or_symbols, timeframe, start, end):
    """
    Fetches stock bars with automatic failover between IEX and SIP feeds.
    Free paper accounts are restricted to IEX during regular market hours,
    which causes 403 Forbidden if SIP is queried directly.
    """
    primary_feed = DataFeed.SIP if str(config.DATA_FEED).lower() == "sip" else DataFeed.IEX
    fallback_feed = DataFeed.IEX if primary_feed == DataFeed.SIP else DataFeed.SIP
    feeds_to_try = [primary_feed, fallback_feed]

    for feed in feeds_to_try:
        try:
            req = StockBarsRequest(
                symbol_or_symbols=symbol_or_symbols,
                timeframe=timeframe,
                start=start,
                end=end,
                feed=feed
            )
            bars = client.get_stock_bars(req)
            if not bars.df.empty:
                return bars.df
        except Exception as e:
            logger.warning(f"Data feed {feed.name} failed for {symbol_or_symbols}: {e}. Retrying fallback...")

    # Return empty DataFrame if all feeds fail
    return pd.DataFrame()

def evaluate_macro_shield():
    """
    Evaluates Macro Regime at 09:45 AM:
    - SPY[09:45] > SMA200_eff AND SPY[09:45] > SMA50 -> BULLISH (Long Engine)
    - SPY[09:45] < SMA200_eff OR SPY[09:45] < SMA50 -> BEARISH (Short Engine)
    """
    client = get_data_client()
    now = datetime.now()
    start_daily = now - timedelta(days=350)
    
    # 1. Fetch SPY Daily Bars for SMA50 and SMA200
    bars_daily = get_stock_bars_safe(client, "SPY", TimeFrame.Day, start_daily, now)
    if bars_daily.empty:
        raise RuntimeError("Failed to fetch SPY daily bars from Alpaca.")

    if isinstance(bars_daily.index, pd.MultiIndex):
        spy_daily = bars_daily.xs("SPY", level=0).sort_index()
    else:
        spy_daily = bars_daily.sort_index()

    # Prior day's moving averages (zero lookahead)
    sma50 = float(spy_daily["close"].rolling(50).mean().iloc[-2]) if len(spy_daily) >= 51 else float(spy_daily["close"].mean())
    sma200 = float(spy_daily["close"].rolling(200).mean().iloc[-2]) if len(spy_daily) >= 201 else sma50
    prev_close = float(spy_daily["close"].iloc[-2])

    # 2. Fetch SPY Intraday Minute Bars up to 09:45 AM
    today_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    bars_1m = get_stock_bars_safe(client, "SPY", TimeFrame.Minute, today_open - timedelta(minutes=10), now)
    
    if not bars_1m.empty:
        if isinstance(bars_1m.index, pd.MultiIndex):
            spy_1m = bars_1m.xs("SPY", level=0).sort_index()
        else:
            spy_1m = bars_1m.sort_index()
        spy_0945 = float(spy_1m["close"].iloc[-1])
    else:
        spy_0945 = float(spy_daily["close"].iloc[-1])

    is_bull = (spy_0945 > sma200) and (spy_0945 > sma50)
    is_bear = (spy_0945 < sma200) or (spy_0945 < sma50)

    regime = "BULLISH" if is_bull else ("BEARISH" if is_bear else "NEUTRAL")
    logger.info(f"SPY 09:45: ${spy_0945:.2f} | SMA50: ${sma50:.2f} | SMA200: ${sma200:.2f} => REGIME: {regime}")

    return {
        "regime": regime,
        "spy_0945": spy_0945,
        "sma50": sma50,
        "sma200": sma200,
        "prev_close": prev_close
    }

def scan_candidates(macro_info):
    """
    Screens universe for #1 Long Leader (Bullish Regime) or #1 Short Laggard (Bearish Regime).
    """
    regime = macro_info["regime"]
    if regime == "NEUTRAL":
        logger.info("Macro regime is NEUTRAL. Remaining 100% Cash.")
        return None

    client = get_data_client()
    now = datetime.now()
    today_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    start_daily = now - timedelta(days=90)

    candidates = []
    logger.info(f"Scanning {len(config.UNIVERSE)} assets for {regime} setups...")

    for sym in config.UNIVERSE:
        if sym == "SPY":
            continue
        try:
            # 1. Daily bars for SMA50 and ATR
            d_df = get_stock_bars_safe(client, sym, TimeFrame.Day, start_daily, now)
            if d_df.empty:
                continue
            if isinstance(d_df.index, pd.MultiIndex):
                d_df = d_df.xs(sym, level=0).sort_index()
            else:
                d_df = d_df.sort_index()

            if len(d_df) < 51:
                continue

            stock_sma50 = float(d_df["close"].rolling(50).mean().iloc[-2])
            prev_close = float(d_df["close"].iloc[-2])
            vol_sma20 = float(d_df["volume"].rolling(20).mean().iloc[-2])
            
            # ATR 20
            high_low = d_df["high"] - d_df["low"]
            high_cp = (d_df["high"] - d_df["close"].shift(1)).abs()
            low_cp = (d_df["low"] - d_df["close"].shift(1)).abs()
            tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
            atr20 = float(tr.rolling(20).mean().iloc[-2])
            atr_pct = (atr20 / prev_close) if prev_close > 0 else 0.0

            if atr_pct < config.MIN_ATR_PCT:
                continue

            # 2. Intraday 15-min bars (09:30 - 09:45 AM)
            m_df = get_stock_bars_safe(client, sym, TimeFrame.Minute, today_open - timedelta(minutes=5), now)
            if m_df.empty:
                continue
            if isinstance(m_df.index, pd.MultiIndex):
                m_df = m_df.xs(sym, level=0).sort_index()
            else:
                m_df = m_df.sort_index()

            if len(m_df) < 2:
                continue

            day_open = float(m_df["open"].iloc[0])
            or15_high = float(m_df["high"].max())
            or15_low = float(m_df["low"].min())
            or15_close = float(m_df["close"].iloc[-1])
            or15_volume = float(m_df["volume"].sum())

            gap_pct = (day_open / prev_close) - 1.0
            expected_vol15 = vol_sma20 * (15.0 / 390.0)
            rvol_15 = (or15_volume / expected_vol15) if expected_vol15 > 0 else 1.0

            if rvol_15 < config.MIN_RVOL_15:
                continue

            # Evaluation by Direction
            if regime == "BULLISH":
                # Long Filters: Day_Open > SMA50, Gap >= +0.3%
                if (day_open > stock_sma50) and (gap_pct >= config.MIN_GAP_PCT):
                    is_green = or15_close > day_open
                    closeness = (or15_close / or15_high) if or15_high > 0 else 0.0
                    score = gap_pct * rvol_15 * (closeness ** 2) * (1.5 if is_green else 0.5)
                    candidates.append({
                        "symbol": sym,
                        "direction": "LONG",
                        "score": score,
                        "entry_stop": or15_high,
                        "stop_loss": or15_high * (1.0 - config.STOP_LOSS_PCT),
                        "take_profit": or15_high * (1.0 + config.TAKE_PROFIT_PCT),
                        "or15_high": or15_high,
                        "or15_low": or15_low,
                        "gap_pct": gap_pct,
                        "rvol_15": rvol_15
                    })

            elif regime == "BEARISH":
                # Short Filters: Day_Open < SMA50, Gap <= -0.3%
                if (day_open < stock_sma50) and (gap_pct <= -config.MIN_GAP_PCT):
                    is_red = or15_close < day_open
                    closeness = (or15_low / or15_close) if or15_close > 0 else 0.0
                    score = abs(gap_pct) * rvol_15 * (closeness ** 2) * (1.5 if is_red else 0.5)
                    candidates.append({
                        "symbol": sym,
                        "direction": "SHORT",
                        "score": score,
                        "entry_stop": or15_low,
                        "stop_loss": or15_low * (1.0 + config.STOP_LOSS_PCT),
                        "take_profit": or15_low * (1.0 - config.TAKE_PROFIT_PCT),
                        "or15_high": or15_high,
                        "or15_low": or15_low,
                        "gap_pct": gap_pct,
                        "rvol_15": rvol_15
                    })

        except Exception as e:
            logger.debug(f"Skipping {sym}: {e}")
            continue

    if not candidates:
        logger.info(f"No qualifying {regime} candidates found today.")
        return None

    # Rank 1 Selection
    candidates.sort(key=lambda x: x["score"], reverse=True)
    best = candidates[0]
    logger.info(f"Selected Rank #1 {best['direction']} Candidate: {best['symbol']} (Score: {best['score']:.4f}, Stop Entry: ${best['entry_stop']:.2f})")
    return best

def run_scan():
    state = state_manager.load_state()
    macro = evaluate_macro_shield()
    best_candidate = scan_candidates(macro)

    state["date"] = datetime.now().strftime("%Y-%m-%d")
    state["macro_regime"] = macro["regime"]
    state["spy_0945"] = macro["spy_0945"]
    state["spy_sma50"] = macro["sma50"]
    state["spy_sma200"] = macro["sma200"]

    if best_candidate:
        state["selected_candidate"] = best_candidate["symbol"]
        state["direction"] = best_candidate["direction"]
        state["entry_stop_price"] = best_candidate["entry_stop"]
        state["stop_loss_price"] = best_candidate["stop_loss"]
        state["take_profit_price"] = best_candidate["take_profit"]
        state["order_status"] = "PENDING_ENTRY"
    else:
        state["selected_candidate"] = None
        state["direction"] = None
        state["order_status"] = "NO_SETUP"

    state_manager.save_state(state)
    return best_candidate
