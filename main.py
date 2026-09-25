"""
Strategy #3: Dual-Regime Long/Short Day Trading Bot
CLI Interface, Early Warmup & 09:45:00 AM Precision Synchronization
"""

import sys
import time
import argparse
import logging
from datetime import datetime, timezone

from alpaca.trading.client import TradingClient

import config
import state_manager
import scanner
import executor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("DualRegime.Main")

def sync_to_target_time(target_hour_utc=13, target_minute_utc=45, target_second_utc=0):
    """
    Precision countdown synchronization to hit 09:45:00.000 AM EDT (13:45:00 UTC) sharp.
    Pre-sleeps with periodic logging, then precision-spins for the last 2 seconds.
    """
    now = datetime.now(timezone.utc)
    target = now.replace(
        hour=target_hour_utc,
        minute=target_minute_utc,
        second=target_second_utc,
        microsecond=0
    )

    remaining = (target - now).total_seconds()
    if remaining <= 0:
        logger.info(f"Target timestamp ({target.strftime('%H:%M:%S')} UTC) already reached. Executing immediately.")
        return

    logger.info(f"Synchronizing to target execution time {target.strftime('%H:%M:%S')} UTC (09:45:00 AM EDT sharp). Remaining: {remaining:.1f}s")

    while remaining > 3.0:
        sleep_dur = min(15.0, remaining - 2.0)
        time.sleep(sleep_dur)
        now = datetime.now(timezone.utc)
        remaining = (target - now).total_seconds()
        logger.info(f"Countdown to 09:45:00 AM EDT: {remaining:.1f} seconds remaining...")

    # High-precision spin for final seconds
    while datetime.now(timezone.utc) < target:
        time.sleep(0.002)

    awakened = datetime.now(timezone.utc)
    logger.info(f"TARGET TIME REACHED! Awakened at {awakened.strftime('%H:%M:%S.%f')[:-3]} UTC. Triggering scan...")

def show_status():
    print("=" * 80)
    print(" STRATEGY #3: DUAL-REGIME LONG/SHORT DAY TRADER - SYSTEM STATUS ")
    print("=" * 80)
    
    try:
        client = TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.ALPACA_PAPER)
        account = client.get_account()
        positions = client.get_all_positions()
        orders = client.get_orders()
        
        print(f"Alpaca Mode:          {'PAPER TRADING' if config.ALPACA_PAPER else 'LIVE TRADING'}")
        print(f"Account Number:       {account.account_number}")
        print(f"Account Status:       {account.status}")
        print(f"Account Equity:       ${float(account.equity):,.2f}")
        print(f"Cash Balance:         ${float(account.cash):,.2f}")
        print(f"Buying Power:         ${float(account.buying_power):,.2f}")
        print(f"Active Positions:     {len(positions)}")
        for p in positions:
            print(f"   -> {p.symbol:<6} ({p.side.upper()}) | Qty: {p.qty:>6} | Current Price: ${float(p.current_price):>8.2f} | P/L: ${float(p.unrealized_pl):>8.2f}")
        print(f"Open Orders:          {len(orders)}")
        for o in orders[:20]:
            print(f"   -> {o.symbol:<6} | {o.side.upper()} {o.type.upper()} | Qty: {o.qty} | Stop: ${float(o.stop_price or 0):.2f} | Status: {o.status}")
        if len(orders) > 20:
            print(f"   ... and {len(orders) - 20} more open orders.")
    except Exception as e:
        print(f"Error querying Alpaca account: {e}")
        
    state = state_manager.load_state()
    print("-" * 80)
    print(f"Date:                 {state.get('date', 'UNKNOWN')}")
    print(f"Macro Regime:         {state.get('macro_regime', 'UNKNOWN')}")
    spy_0945 = state.get('spy_0945') or 0.0
    spy_sma50 = state.get('spy_sma50') or 0.0
    spy_sma200 = state.get('spy_sma200') or 0.0
    print(f"SPY Price (09:45):    ${spy_0945:.2f} (50 SMA: ${spy_sma50:.2f} | 200 SMA: ${spy_sma200:.2f})")
    print(f"Qualified Count:      {state.get('qualified_count', 0)}")
    print(f"Qualified Tickers:    {', '.join(state.get('qualified_candidates', [])[:10])}")
    print(f"Order Status:         {state.get('order_status', 'IDLE')}")
    print(f"Committed Capital:    ${state.get('capital_committed', 0.0):,.2f}")
    print(f"Last Updated:         {state.get('last_updated', 'Never')}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Strategy #3: Dual-Regime Long/Short Day Trading Bot")
    parser.add_argument("--warmup", action="store_true", help="Run 09:40 AM pre-market warmup, pre-fetch daily metrics, and sync to 09:45:00 AM sharp")
    parser.add_argument("--scan", action="store_true", help="Run 09:45 AM scan and multi-order placement directly")
    parser.add_argument("--cutoff", action="store_true", help="Run 11:30 AM order cutoff to cancel unfilled entries")
    parser.add_argument("--moc", action="store_true", help="Run 15:55 PM Market-on-Close liquidation (100% flat)")
    parser.add_argument("--status", action="store_true", help="Display current account and strategy status")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without submitting real orders")
    parser.add_argument("--test", action="store_true", help="Test connection and credentials")
    
    args = parser.parse_args()
    
    if args.status or args.test:
        show_status()
    elif args.warmup:
        logger.info("Initializing 09:40 AM Pre-Market Warmup Cycle...")
        # 1. Pre-fetch daily bars during warmup window (0 market seconds)
        daily_cache = scanner.fetch_daily_metrics_batch(config.UNIVERSE)
        # 2. Synchronize to 09:45:00 AM EDT (13:45:00 UTC) sharp
        sync_to_target_time(target_hour_utc=13, target_minute_utc=45, target_second_utc=0)
        # 3. Pull 15m intraday bars and screen
        candidates = scanner.run_scan(daily_cache=daily_cache)
        # 4. Multi-order throttled submission
        if candidates:
            executor.submit_entry_brackets_multi(candidates, dry_run=args.dry_run)
    elif args.scan:
        candidates = scanner.run_scan()
        if candidates:
            executor.submit_entry_brackets_multi(candidates, dry_run=args.dry_run)
    elif args.cutoff:
        executor.cancel_unfilled_entries()
    elif args.moc:
        executor.market_on_close_liquidation()
    else:
        show_status()

if __name__ == "__main__":
    main()
