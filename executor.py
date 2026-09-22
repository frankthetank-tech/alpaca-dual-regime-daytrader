"""
Strategy #3: Order Execution Engine
Places Native Alpaca Bracket Stop Orders, Manages 11:30 AM Expiry, & 15:55 PM MOC Liquidation
"""

import math
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    StopOrderRequest,
    TakeProfitRequest,
    StopLossRequest,
    OrderClass,
    TimeInForce,
    OrderSide
)

import config
import state_manager

logger = logging.getLogger("DualRegime.Executor")

def get_trading_client():
    return TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.ALPACA_PAPER)

def submit_entry_bracket(candidate, dry_run=False):
    """
    Submits a native bracket stop order to Alpaca matching engine.
    - Long: Buy-Stop at OR15_High with Stop (-1.2%) and Limit (+3.5%)
    - Short: Sell-Stop at OR15_Low with Stop (+1.2%) and Limit (-3.5%)
    """
    if not candidate:
        logger.info("No candidate provided to execute.")
        return None

    client = get_trading_client()
    account = client.get_account()
    equity = float(account.equity)
    cash = float(account.cash)

    alloc_dollars = min(equity, cash) * config.MAX_ALLOCATION_PCT
    entry_price = candidate["entry_stop"]
    
    # Calculate integer shares
    qty = math.floor(alloc_dollars / entry_price)
    if qty <= 0:
        logger.warning(f"Calculated quantity is 0 for {candidate['symbol']} at ${entry_price:.2f}. Insufficient capital.")
        return None

    side = OrderSide.BUY if candidate["direction"] == "LONG" else OrderSide.SELL
    stop_price = round(candidate["entry_stop"], 2)
    stop_loss_px = round(candidate["stop_loss"], 2)
    take_profit_px = round(candidate["take_profit"], 2)

    logger.info(
        f"Preparing {candidate['direction']} Bracket Order: {qty} shares of {candidate['symbol']} "
        f"@ Stop Trigger: ${stop_price:.2f} | Stop Loss: ${stop_loss_px:.2f} | Take Profit: ${take_profit_px:.2f}"
    )

    if dry_run:
        logger.info("[DRY-RUN] Bracket order simulated successfully. No live order submitted.")
        return {"id": "dry-run-order", "symbol": candidate["symbol"], "qty": qty}

    try:
        req = StopOrderRequest(
            symbol=candidate["symbol"],
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY,
            stop_price=stop_price,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=take_profit_px),
            stop_loss=StopLossRequest(stop_price=stop_loss_px)
        )
        order = client.submit_order(req)
        logger.info(f"Bracket order submitted successfully! Order ID: {order.id}")

        state = state_manager.load_state()
        state["order_status"] = "SUBMITTED"
        state["order_id"] = str(order.id)
        state_manager.save_state(state)
        return order
    except Exception as e:
        logger.error(f"Failed to submit bracket order: {e}")
        return None

def cancel_unfilled_entries():
    """
    Called at 11:30 AM EST:
    Cancels any resting unfilled entry stop orders so capital remains 100% cash.
    """
    client = get_trading_client()
    state = state_manager.load_state()

    try:
        orders = client.get_orders()
        cancelled_count = 0
        for o in orders:
            # If the order is still open or held
            if o.status in ("new", "accepted", "pending_new", "held"):
                client.cancel_order_by_id(o.id)
                cancelled_count += 1
                logger.info(f"Cancelled unfilled resting order: {o.id} ({o.symbol})")

        state["order_status"] = "EXPIRED" if cancelled_count > 0 else state.get("order_status")
        state_manager.save_state(state)
        logger.info(f"11:30 AM Cutoff check complete. Cancelled {cancelled_count} unfilled orders.")
    except Exception as e:
        logger.error(f"Error during 11:30 AM order cutoff: {e}")

def market_on_close_liquidation():
    """
    Called at 15:55 PM EST:
    Closes all open positions and cancels any resting orders.
    Enforces 100% Cash overnight (zero overnight risk).
    """
    client = get_trading_client()
    state = state_manager.load_state()

    try:
        # Cancel all open orders first
        client.cancel_orders()
        logger.info("Cancelled all open orders before MOC liquidation.")

        # Close all active positions
        closed_positions = client.close_all_positions(cancel_orders=True)
        logger.info(f"Liquidated {len(closed_positions)} open positions via Market-on-Close. Account is 100% Cash.")

        state["order_status"] = "CLOSED_MOC"
        state_manager.save_state(state)
    except Exception as e:
        logger.error(f"Error during MOC liquidation: {e}")
