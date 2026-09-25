"""
Strategy #3: Vectorized High-Performance Scanner & Signal Engine
Evaluates 09:45 AM Dual-Regime Macro Shield and Ranks 500 Qualified Candidates
Optimized with Vectorized Batch Market Data Retrieval & Sub-Second Execution
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

import config
import state_manager

logger = logging.getLogger("DualRegime.Scanner")
NY_TZ = ZoneInfo("America/New_York")

def get_data_client():
    return StockHistoricalDataClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY)

def get_feed():
    return DataFeed.SIP if str(config.DATA_FEED).lower() == "sip" else DataFeed.IEX

def evaluate_macro_shield():
    """
    Evaluates Macro Regime at 09:45 AM:
    - SPY[09:45] > SMA200 AND SPY[09:45] > SMA50 -> BULLISH (Long Engine)
    - SPY[09:45] < SMA200 OR SPY[09:45] < SMA50  -> BEARISH (Short Engine)
    """
    client = get_data_client()
    feed = get_feed()
    now_ny = datetime.now(NY_TZ)
    start_daily = now_ny - timedelta(days=350)
    
    # 1. Fetch SPY Daily Bars for SMA50 and SMA200
    try:
        req = StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Day, start=start_daily, end=now_ny, feed=feed)
        bars_daily = client.get_stock_bars(req).df
    except Exception as e:
        logger.warning(f"Failed to fetch SPY with {feed.name}: {e}. Retrying fallback...")
        alt_feed = DataFeed.IEX if feed == DataFeed.SIP else DataFeed.SIP
        req = StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Day, start=start_daily, end=now_ny, feed=alt_feed)
        bars_daily = client.get_stock_bars(req).df

    if isinstance(bars_daily.index, pd.MultiIndex):
        spy_daily = bars_daily.xs("SPY", level=0).sort_index()
    else:
        spy_daily = bars_daily.sort_index()

    sma50 = float(spy_daily["close"].rolling(50).mean().iloc[-2]) if len(spy_daily) >= 51 else float(spy_daily["close"].mean())
    sma200 = float(spy_daily["close"].rolling(200).mean().iloc[-2]) if len(spy_daily) >= 201 else sma50
    prev_close = float(spy_daily["close"].iloc[-2])

    # 2. Fetch SPY Intraday Minute Bars up to 09:45 AM
    today_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    today_or15 = now_ny.replace(hour=9, minute=45, second=0, microsecond=0)
    end_query = now_ny if now_ny < today_or15 else today_or15

    try:
        req_1m = StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Minute, start=today_open - timedelta(minutes=5), end=end_query, feed=feed)
        bars_1m = client.get_stock_bars(req_1m).df
    except Exception:
        bars_1m = pd.DataFrame()

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

def fetch_daily_metrics_batch(symbols=None):
    """
    Pre-market Warmup Batch:
    Fetches 90-day daily bars for all 500 symbols in a single vectorized batch request.
    Computes SMA50, ATR20, ATR%, Volume SMA20, and Previous Close.
    Benchmarked at ~1.87s for 500 tickers.
    """
    if symbols is None:
        symbols = config.UNIVERSE

    client = get_data_client()
    feed = get_feed()
    now_ny = datetime.now(NY_TZ)
    start_daily = now_ny - timedelta(days=95)

    logger.info(f"Pre-fetching daily metrics for {len(symbols)} tickers in vectorized batch ({feed.name})...")
    req = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=start_daily,
        end=now_ny,
        feed=feed
    )
    bars_df = client.get_stock_bars(req).df

    if bars_df.empty:
        logger.error("Daily batch query returned empty DataFrame!")
        return {}

    metrics = {}
    grouped = bars_df.groupby(level=0)
    for sym, df_sym in grouped:
        if len(df_sym) < 51:
            continue
        try:
            closes = df_sym["close"]
            highs = df_sym["high"]
            lows = df_sym["low"]
            volumes = df_sym["volume"]

            sma50 = float(closes.rolling(50).mean().iloc[-2])
            prev_close = float(closes.iloc[-2])
            vol_sma20 = float(volumes.rolling(20).mean().iloc[-2])

            # Vectorized ATR 20
            h_l = highs - lows
            h_cp = (highs - closes.shift(1)).abs()
            l_cp = (lows - closes.shift(1)).abs()
            tr = pd.concat([h_l, h_cp, l_cp], axis=1).max(axis=1)
            atr20 = float(tr.rolling(20).mean().iloc[-2])
            atr_pct = (atr20 / prev_close) if prev_close > 0 else 0.0

            metrics[sym] = {
                "sma50": sma50,
                "prev_close": prev_close,
                "vol_sma20": vol_sma20,
                "atr20": atr20,
                "atr_pct": atr_pct
            }
        except Exception:
            continue

    logger.info(f"Daily metrics pre-computed for {len(metrics)} valid symbols.")
    return metrics

def fetch_intraday_or15_batch(symbols=None):
    """
    09:45:00 AM Precision Batch:
    Fetches 15-minute 1-min bars for all 500 symbols in a single vectorized batch request.
    Computes Day Open, OR15 High, OR15 Low, OR15 Close, and OR15 Volume.
    Benchmarked at ~0.20s for 500 tickers.
    """
    if symbols is None:
        symbols = config.UNIVERSE

    client = get_data_client()
    feed = get_feed()
    now_ny = datetime.now(NY_TZ)
    today_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    today_or15 = now_ny.replace(hour=9, minute=45, second=0, microsecond=0)
    query_end = now_ny if now_ny < today_or15 else today_or15

    logger.info(f"Pulling 15m intraday bars for {len(symbols)} tickers in vectorized batch ({feed.name})...")
    req = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Minute,
        start=today_open,
        end=query_end,
        feed=feed
    )
    bars_df = client.get_stock_bars(req).df

    if bars_df.empty:
        logger.error("Intraday 15m batch query returned empty DataFrame!")
        return {}

    intraday = {}
    grouped = bars_df.groupby(level=0)
    for sym, df_sym in grouped:
        if len(df_sym) < 2:
            continue
        try:
            day_open = float(df_sym["open"].iloc[0])
            or15_high = float(df_sym["high"].max())
            or15_low = float(df_sym["low"].min())
            or15_close = float(df_sym["close"].iloc[-1])
            or15_volume = float(df_sym["volume"].sum())

            intraday[sym] = {
                "day_open": day_open,
                "or15_high": or15_high,
                "or15_low": or15_low,
                "or15_close": or15_close,
                "or15_volume": or15_volume
            }
        except Exception:
            continue

    logger.info(f"Intraday 15m bars retrieved for {len(intraday)} symbols.")
    return intraday

def scan_all_candidates(macro_info, daily_cache=None):
    """
    Screens the 500-ticker universe:
    1. Reuses pre-fetched daily metrics (or fetches in batch if uncached).
    2. Pulls 15m intraday bars in batch.
    3. Filters for 100% compliant Strategy #3 setups.
    4. SORTS QUALIFIED CANDIDATES BY SHARE PRICE ASCENDING (lowest dollar value first)
       to maximize the quantity of tickers for the single full-share execution engine.
    """
    regime = macro_info["regime"]
    if regime == "NEUTRAL":
        logger.info("Macro regime is NEUTRAL. Remaining 100% Cash.")
        return []

    # 1. Daily metrics
    if daily_cache and len(daily_cache) > 0:
        logger.info(f"Using pre-cached daily metrics for {len(daily_cache)} symbols.")
        daily_metrics = daily_cache
    else:
        daily_metrics = fetch_daily_metrics_batch(config.UNIVERSE)

    # 2. Intraday 15-min bars
    intraday_data = fetch_intraday_or15_batch(config.UNIVERSE)

    qualified_candidates = []
    logger.info(f"Screening cross-section for {regime} setups...")

    for sym in config.UNIVERSE:
        if sym == "SPY":
            continue
        d = daily_metrics.get(sym)
        m = intraday_data.get(sym)
        if not d or not m:
            continue

        # Filter 1: Minimum ATR% >= 1.5%
        if d["atr_pct"] < config.MIN_ATR_PCT:
            continue

        # Filter 2: RVOL 15 >= 1.25x
        expected_vol15 = d["vol_sma20"] * (15.0 / 390.0)
        rvol_15 = (m["or15_volume"] / expected_vol15) if expected_vol15 > 0 else 1.0
        if rvol_15 < config.MIN_RVOL_15:
            continue

        prev_close = d["prev_close"]
        day_open = m["day_open"]
        gap_pct = (day_open / prev_close) - 1.0

        if regime == "BULLISH":
            # Long Rules: Day_Open > SMA50, Gap >= +0.3%
            if (day_open > d["sma50"]) and (gap_pct >= config.MIN_GAP_PCT):
                is_green = m["or15_close"] > day_open
                closeness = (m["or15_close"] / m["or15_high"]) if m["or15_high"] > 0 else 0.0
                score = gap_pct * rvol_15 * (closeness ** 2) * (1.5 if is_green else 0.5)
                entry_stop = round(m["or15_high"], 2)

                qualified_candidates.append({
                    "symbol": sym,
                    "direction": "LONG",
                    "score": score,
                    "entry_stop": entry_stop,
                    "stop_loss": round(entry_stop * (1.0 - config.STOP_LOSS_PCT), 2),
                    "take_profit": round(entry_stop * (1.0 + config.TAKE_PROFIT_PCT), 2),
                    "or15_high": m["or15_high"],
                    "or15_low": m["or15_low"],
                    "gap_pct": gap_pct,
                    "rvol_15": rvol_15,
                    "atr_pct": d["atr_pct"]
                })

        elif regime == "BEARISH":
            # Short Rules: Day_Open < SMA50, Gap <= -0.3%
            if (day_open < d["sma50"]) and (gap_pct <= -config.MIN_GAP_PCT):
                is_red = m["or15_close"] < day_open
                closeness = (m["or15_low"] / m["or15_close"]) if m["or15_close"] > 0 else 0.0
                score = abs(gap_pct) * rvol_15 * (closeness ** 2) * (1.5 if is_red else 0.5)
                entry_stop = round(m["or15_low"], 2)

                qualified_candidates.append({
                    "symbol": sym,
                    "direction": "SHORT",
                    "score": score,
                    "entry_stop": entry_stop,
                    "stop_loss": round(entry_stop * (1.0 + config.STOP_LOSS_PCT), 2),
                    "take_profit": round(entry_stop * (1.0 - config.TAKE_PROFIT_PCT), 2),
                    "or15_high": m["or15_high"],
                    "or15_low": m["or15_low"],
                    "gap_pct": gap_pct,
                    "rvol_15": rvol_15,
                    "atr_pct": d["atr_pct"]
                })

    logger.info(f"Total fully qualified {regime} candidates found: {len(qualified_candidates)}")

    # USER DIRECTIVE: Start orders with lowest dollar value share, then next lowest, and so on
    # to maximize the quantity of tickers for the single full-share execution engine.
    qualified_candidates.sort(key=lambda x: x["entry_stop"], reverse=False)

    for i, c in enumerate(qualified_candidates[:15], start=1):
        logger.info(f"   Candidate #{i}: {c['symbol']:<5} | Share Price: ${c['entry_stop']:>7.2f} | Score: {c['score']:.4f} | RVOL: {c['rvol_15']:.2f}x")

    return qualified_candidates

def run_scan(daily_cache=None):
    import audit_logger

    state = state_manager.load_state()
    macro = evaluate_macro_shield()
    candidates = scan_all_candidates(macro, daily_cache=daily_cache)

    date_str = datetime.now(NY_TZ).strftime("%Y-%m-%d")
    state["date"] = date_str
    state["macro_regime"] = macro["regime"]
    state["spy_0945"] = macro["spy_0945"]
    state["spy_sma50"] = macro["sma50"]
    state["spy_sma200"] = macro["sma200"]
    state["qualified_count"] = len(candidates)
    state["qualified_candidates"] = [c["symbol"] for c in candidates[:config.MAX_POSITIONS]]

    if candidates:
        top1 = candidates[0]
        state["selected_candidate"] = top1["symbol"]
        state["direction"] = top1["direction"]
        state["entry_stop_price"] = top1["entry_stop"]
        state["stop_loss_price"] = top1["stop_loss"]
        state["take_profit_price"] = top1["take_profit"]
        state["order_status"] = f"PENDING_{len(candidates)}_ORDERS"
    else:
        state["selected_candidate"] = None
        state["direction"] = None
        state["order_status"] = "NO_SETUP"

    state_manager.save_state(state)

    # Record structured audit event & summary
    audit_logger.record_event("SCAN_COMPLETE", {
        "date": date_str,
        "screened_count": len(config.UNIVERSE),
        "macro_regime": macro["regime"],
        "spy_price": macro["spy_0945"],
        "spy_sma50": macro["sma50"],
        "spy_sma200": macro["sma200"],
        "qualified_count": len(candidates),
        "qualified_candidates": [
            {
                "rank": idx + 1,
                "symbol": c["symbol"],
                "direction": c["direction"],
                "entry_stop": c["entry_stop"],
                "stop_loss": c["stop_loss"],
                "take_profit": c["take_profit"],
                "gap_pct": c["gap_pct"],
                "rvol15": c["rvol_15"],
                "atr_pct": c["atr_pct"],
                "score": c["score"]
            }
            for idx, c in enumerate(candidates[:config.MAX_POSITIONS])
        ]
    })

    audit_logger.update_daily_summary({
        "date": date_str,
        "macro_regime": macro["regime"],
        "spy_0945": macro["spy_0945"],
        "spy_sma50": macro["sma50"],
        "spy_sma200": macro["sma200"],
        "screened_count": len(config.UNIVERSE),
        "qualified_count": len(candidates),
        "status": state["order_status"]
    })

    return candidates
