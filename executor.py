"""
Strategy #3: Order Execution Engine (ORB-15 Cond 4 V2)
Dynamic Account-Tier Sizing & Whole-Share Multi-Order Execution Engine
Places Native Alpaca Bracket Orders, Manages 11:30 AM Cutoff & 15:45 PM MOC Liquidation
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
    Submits native bracket stop orders using Dynamic Account-Tier Sizing (Whole Shares Only).
    - Max positions capped dynamically based on cash equity:
        < $15k: 2 positions max (50% BP each)
        < $50k: 3 positions max (33.3% BP each)
        < $150k: 4 positions max (25% BP each)
        < $500k: 5 positions max (20% BP each)
        >= $500k: 8 positions max (12.5% BP each)
    - Allocates strictly integer whole shares (zero fractional share exposure).
    - Throttled at ORDER_THROTTLE_RATE (6 orders per second).
    """
    if not candidates:
        logger.info("No qualified candidates provided to execute.")
        return []

    client = get_trading_client()
    account = client.get_account()
    cash = float(account.cash)
    
    # Calculate buying power based on configured margin multiplier (default: 2.0x BP / 100% margin)
    broker_bp = float(account.buying_power)
    buying_power = min(cash * config.BUYING_POWER_MULT, broker_bp) if broker_bp > 0 else (cash * config.BUYING_POWER_MULT)

    # Dynamic Account Tier Max Positions
    max_positions = config.get_max_positions(cash)
    selected_candidates = candidates[:max_positions]
    n_pos = len(selected_candidates)

    if n_pos == 0:
        logger.info("Zero candidates selected for execution.")
        return []

    alloc_per_pos = buying_power / n_pos

    logger.info("=" * 80)
    logger.info("BEGINNING DYNAMIC TIER MULTI-ORDER BRACKET PLACEMENT")
    logger.info(f"   Cash Equity:       ${cash:,.2f}")
    logger.info(f"   Buying Power:      ${buying_power:,.2f} ({config.BUYING_POWER_MULT:.1f}x Multiplier)")
    logger.info(f"   Max Positions:     {max_positions} (Dynamic Tier)")
    logger.info(f"   Selected Setups:   {n_pos} candidates")
    logger.info(f"   Alloc per Pos:     ${alloc_per_pos:,.2f}")
    logger.info(f"   Throttle Rate:     {config.ORDER_THROTTLE_RATE} orders/sec")
    logger.info("=" * 80)

    orders_submitted = []
    throttle_sleep = 1.0 / float(config.ORDER_THROTTLE_RATE)
    remaining_bp = buying_power

    for i, candidate in enumerate(selected_candidates, start=1):
        sym = candidate["symbol"]
        entry_price = candidate["entry_stop"]
        direction = candidate["direction"]
        side = OrderSide.BUY if direction == "LONG" else OrderSide.SELL
        stop_price = round(entry_price, 2)
        stop_loss_px = round(candidate["stop_loss"], 2)
        take_profit_px = round(candidate["take_profit"], 2)
        target_pct = candidate.get("target_pct", 0.035)

        # Whole Shares Only (Integer Floor Division)
        qty = int(alloc_per_pos // stop_price)
        if qty <= 0:
            logger.warning(
                f"Candidate #{i} ({sym} @ ${stop_price:.2f}) share price exceeds position allocation (${alloc_per_pos:,.2f}). "
                f"Cannot purchase 1 whole share. Skipping candidate."
            )
            audit_logger.record_event("ORDER_SKIPPED", {
                "symbol": sym,
                "price": stop_price,
                "alloc": alloc_per_pos,
                "reason": "share_price_exceeds_allocation"
            })
            continue

        order_cost = qty * stop_price
        if remaining_bp < order_cost:
            logger.warning(
                f"Candidate #{i} ({sym} x {qty} shs = ${order_cost:,.2f}) exceeds remaining buying power (${remaining_bp:,.2f}). "
                f"Halting further orders."
            )
            break

        logger.info(
            f"[{i}/{n_pos}] Submitting {direction} Bracket: {qty} shs of {sym} @ Stop: ${stop_price:.2f} | "
            f"SL: ${stop_loss_px:.2f} (-1.2%) | TP: ${take_profit_px:.2f} (+{target_pct*100:.2f}%) | "
            f"Cost: ${order_cost:,.2f} | Remaining BP: ${remaining_bp - order_cost:,.2f}"
        )

        if dry_run:
            orders_submitted.append({
                "id": f"dry-run-{sym}",
                "symbol": sym,
                "qty": qty,
                "price": stop_price,
                "direction": direction,
                "cost": order_cost
            })
            remaining_bp -= order_cost
            audit_logger.record_event("ORDER_SUBMITTED", {
                "index": len(orders_submitted),
                "symbol": sym,
                "direction": direction,
                "qty": qty,
                "stop_price": stop_price,
                "sl": stop_loss_px,
                "tp": take_profit_px,
                "order_id": f"dry-run-{sym}",
                "order_cost": order_cost,
                "remaining_bp": remaining_bp
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
                "direction": direction,
                "cost": order_cost
            })
            remaining_bp -= order_cost
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
                "order_cost": order_cost,
                "remaining_bp": remaining_bp
            })

            time.sleep(throttle_sleep)

        except Exception as e:
            logger.error(f"Failed to submit bracket order for {sym}: {e}")
            audit_logger.record_event("ORDER_ERROR", {
                "symbol": sym,
                "error": str(e)
            })
            time.sleep(throttle_sleep)

    total_committed = buying_power - remaining_bp
    logger.info(
        f"Dynamic Bracket Submission Complete! Placed {len(orders_submitted)} orders. "
        f"Total Committed Buying Power: ${total_committed:,.2f} | Remaining BP Reserve: ${remaining_bp:,.2f}"
    )

    state = state_manager.load_state()
    state["order_status"] = f"{len(orders_submitted)}_ORDERS_PLACED"
    state["active_orders"] = orders_submitted
    state["capital_committed"] = total_committed
    state_manager.save_state(state)

    audit_logger.record_event("ORDER_BATCH_COMPLETE", {
        "orders_placed": len(orders_submitted),
        "capital_committed": total_committed,
        "remaining_bp": remaining_bp
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
    Called at 15:45 PM EST:
    Closes all open positions and cancels any resting orders.
    Enforces 100% Cash overnight (zero overnight risk & zero margin interest).
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
