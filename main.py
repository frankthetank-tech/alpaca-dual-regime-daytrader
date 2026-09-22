"""
Strategy #3: Dual-Regime Long/Short Day Trading Bot
CLI Interface & Execution Dispatcher
"""

import sys
import argparse
import logging
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
        for o in orders:
            print(f"   -> {o.symbol:<6} | {o.side.upper()} {o.type.upper()} | Qty: {o.qty} | Stop: ${float(o.stop_price or 0):.2f} | Status: {o.status}")
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
    print(f"Selected Candidate:   {state.get('selected_candidate', 'None')} ({state.get('direction', 'None')})")
    print(f"Entry Stop:           ${state.get('entry_stop_price', 0.0):.2f}")
    print(f"Stop Loss:            ${state.get('stop_loss_price', 0.0):.2f} (-1.2%)")
    print(f"Take Profit:          ${state.get('take_profit_price', 0.0):.2f} (+3.5%)")
    print(f"Order Status:         {state.get('order_status', 'IDLE')}")
    print(f"Last Updated:         {state.get('last_updated', 'Never')}")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Strategy #3: Dual-Regime Long/Short Day Trading Bot")
    parser.add_argument("--scan", action="store_true", help="Run 09:45 AM Macro Shield evaluation and order placement")
    parser.add_argument("--cutoff", action="store_true", help="Run 11:30 AM order cutoff to cancel unfilled entries")
    parser.add_argument("--moc", action="store_true", help="Run 15:55 PM Market-on-Close liquidation (100% flat)")
    parser.add_argument("--status", action="store_true", help="Display current account and strategy status")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without submitting real orders")
    parser.add_argument("--test", action="store_true", help="Test connection and credentials")
    
    args = parser.parse_args()
    
    if args.status or args.test:
        show_status()
    elif args.scan:
        candidate = scanner.run_scan()
        if candidate:
            executor.submit_entry_bracket(candidate, dry_run=args.dry_run)
    elif args.cutoff:
        executor.cancel_unfilled_entries()
    elif args.moc:
        executor.market_on_close_liquidation()
    else:
        show_status()

if __name__ == "__main__":
    main()
