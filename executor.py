"""
Strategy #3: Order Execution Engine
Single Full-Share Multi-Order Execution Engine with 6 Orders/Sec Throttling
Places Native Alpaca Bracket Orders (qty=1), Manages 11:30 AM Cutoff & 15:55 PM MOC Liquidation
"""

import math
import time
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
import audit_logger

logger = logging.getLogger("DualRegime.Executor")

def get_trading_client():
    return TradingClient(config.ALPACA_API_KEY, config.ALPACA_SECRET_KEY, paper=config.ALPACA_PAPER)

def submit_entry_brackets_multi(candidates, dry_run=False):
    """
    Submits native bracket stop orders for 1 full share (qty=1) across the maximum
    quantity of qualified tickers possible with the available cash balance (capped at MAX_POSITIONS).
    Throttled at ORDER_THROTTLE_RATE (6 orders per second) to stay well under Alpaca rate limits.
    """
    if not candidates:
        logger.info("No qualified candidates provided to execute.")
        return []

    client = get_trading_client()
    account = client.get_account()
    cash = float(account.cash) * config.MAX_ALLOCATION_PCT
    remaining_cash = cash

    logger.info(
        f"Beginning Multi-Order Placement | Available Cash: ${cash:,.2f} | "
        f"Qualified Candidates: {len(candidates)} | Max Positions: {config.MAX_POSITIONS} | "
        f"Throttle: {config.ORDER_THROTTLE_RATE} orders/sec"
    )

    orders_submitted = []
    throttle_sleep = 1.0 / float(config.ORDER_THROTTLE_RATE)

    for i, candidate in enumerate(candidates, start=1):
        if len(orders_submitted) >= config.MAX_POSITIONS:
            logger.info(f"Reached MAX_POSITIONS cap ({config.MAX_POSITIONS} orders). Halting order submissions.")
            break

        sym = candidate["symbol"]
        entry_price = candidate["entry_stop"]
        direction = candidate["direction"]
        side = OrderSide.BUY if direction == "LONG" else OrderSide.SELL
        stop_price = round(entry_price, 2)
        stop_loss_px = round(candidate["stop_loss"], 2)
        take_profit_px = round(candidate["take_profit"], 2)

        # Check cash balance for 1 full share
        if remaining_cash < stop_price:
            logger.info(
                f"Candidate #{i} ({sym} @ ${stop_price:.2f}) exceeds remaining cash (${remaining_cash:.2f}). "
                f"Since candidates are sorted by price ascending, halting submissions."
            )
            audit_logger.record_event("ORDER_SKIPPED", {
                "symbol": sym,
                "price": stop_price,
                "remaining_cash": remaining_cash,
                "reason": "exceeds_remaining_cash"
            })
            break

        qty = config.ORDER_QTY  # Strictly 1 full share

        logger.info(
            f"[{len(orders_submitted) + 1}/{min(len(candidates), config.MAX_POSITIONS)}] Submitting {direction} Bracket: "
            f"{qty} share of {sym} @ Stop: ${stop_price:.2f} | SL: ${stop_loss_px:.2f} (-1.2%) | TP: ${take_profit_px:.2f} (+3.5%) | "
            f"Remaining Cash: ${remaining_cash - stop_price:.2f}"
        )

        if dry_run:
            orders_submitted.append({
                "id": f"dry-run-{sym}",
                "symbol": sym,
                "qty": qty,
                "price": stop_price,
                "direction": direction
            })
            remaining_cash -= stop_price
            audit_logger.record_event("ORDER_SUBMITTED", {
                "index": len(orders_submitted),
                "symbol": sym,
                "direction": direction,
                "qty": qty,
                "stop_price": stop_price,
                "sl": stop_loss_px,
                "tp": take_profit_px,
                "order_id": f"dry-run-{sym}",
                "remaining_cash": remaining_cash
            })
            time.sleep(0.01)
            continue

        try:
            req = StopOrderRequest(
                symbol=sym,
                qty=qty,
                side=side,
                time_in_force=TimeInForce.DAY,
                stop_price=stop_price,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=take_profit_px),
                stop_loss=StopLossRequest(stop_price=stop_loss_px)
            )
            order = client.submit_order(req)
            orders_submitted.append({
                "id": str(order.id),
                "symbol": sym,
                "qty": qty,
                "price": stop_price,
                "direction": direction
            })
            remaining_cash -= stop_price
            logger.info(f"   -> Accepted by Alpaca matching engine! Order ID: {order.id}")

            audit_logger.record_event("ORDER_SUBMITTED", {
                "index": len(orders_submitted),
                "symbol": sym,
                "direction": direction,
                "qty": qty,
                "stop_price": stop_price,
                "sl": stop_loss_px,
                "tp": take_profit_px,
                "order_id": str(order.id),
                "remaining_cash": remaining_cash
            })

            # Throttling delay to guarantee compliance with 10 req/s burst limit
            time.sleep(throttle_sleep)

        except Exception as e:
            logger.error(f"Failed to submit bracket order for {sym}: {e}")
            audit_logger.record_event("ORDER_ERROR", {
                "symbol": sym,
                "error": str(e)
            })
            # Still sleep to prevent burst on errors
            time.sleep(throttle_sleep)

    total_committed = cash - remaining_cash
    logger.info(
        f"Multi-Order Submission Complete! Placed {len(orders_submitted)} orders. "
        f"Total Capital Committed: ${total_committed:,.2f} | Remaining Cash Reserve: ${remaining_cash:,.2f}"
    )

    state = state_manager.load_state()
    state["order_status"] = f"{len(orders_submitted)}_ORDERS_PLACED"
    state["active_orders"] = orders_submitted
    state["capital_committed"] = total_committed
    state_manager.save_state(state)

    audit_logger.record_event("ORDER_BATCH_COMPLETE", {
        "orders_placed": len(orders_submitted),
        "capital_committed": total_committed,
        "remaining_cash": remaining_cash
    })
    audit_logger.update_daily_summary({
        "orders_placed": len(orders_submitted),
        "capital_committed": total_committed,
        "status": state["order_status"]
    })

    return orders_submitted

def cancel_unfilled_entries():
    """
    Called at 11:30 AM EST:
    Cancels any resting unfilled entry stop orders across all positions.
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

        audit_logger.record_event("CUTOFF_1130", {
            "cancelled_count": cancelled_count
        })
        audit_logger.update_daily_summary({
            "cancelled_cutoff": cancelled_count,
            "status": state["order_status"]
        })
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

        audit_logger.record_event("MOC_LIQUIDATION", {
            "closed_count": len(closed_positions)
        })
        audit_logger.update_daily_summary({
            "closed_moc": len(closed_positions),
            "status": state["order_status"]
        })
    except Exception as e:
        logger.error(f"Error during MOC liquidation: {e}")
