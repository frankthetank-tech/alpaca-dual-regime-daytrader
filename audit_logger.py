"""
Strategy #3: Comprehensive Audit & Daily Logging Engine
Maintains daily log files, structured event ledgers, and session summaries for 100% transparency.
"""

import os
import sys
import json
import csv
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

EASTERN_TZ = ZoneInfo("America/New_York")

AUDIT_DIR = os.path.join(os.path.dirname(__file__), "data", "audit")
LOGS_DIR = os.path.join(AUDIT_DIR, "logs")
EVENTS_DIR = os.path.join(AUDIT_DIR, "events")
SUMMARY_CSV = os.path.join(AUDIT_DIR, "daily_summary.csv")

def get_current_date_ny():
    return datetime.now(EASTERN_TZ).strftime("%Y-%m-%d")

def ensure_directories():
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(EVENTS_DIR, exist_ok=True)

def setup_logging(date_str=None):
    """
    Sets up root and strategy logging with two outputs:
    1. Daily dedicated log file: data/audit/logs/YYYY-MM-DD.log
    2. Standard console output: stdout (for live runs & CI/CD logs)
    """
    ensure_directories()
    if not date_str:
        date_str = get_current_date_ny()

    log_file = os.path.join(LOGS_DIR, f"{date_str}.log")

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to prevent duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Daily File Handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    logger = logging.getLogger("DualRegime.Audit")
    logger.info(f"Initialized daily audit logging -> {log_file}")
    return logger

def record_event(event_type, data, date_str=None):
    """
    Appends an atomic structured record to data/audit/events/YYYY-MM-DD.jsonl
    """
    ensure_directories()
    if not date_str:
        date_str = get_current_date_ny()

    events_file = os.path.join(EVENTS_DIR, f"{date_str}.jsonl")
    now_utc = datetime.now(timezone.utc).isoformat()
    now_ny = datetime.now(EASTERN_TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    record = {
        "timestamp_utc": now_utc,
        "timestamp_ny": now_ny,
        "event_type": event_type,
        "payload": data
    }

    try:
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception as e:
        logging.getLogger("DualRegime.Audit").error(f"Failed to record event {event_type}: {e}")

def update_daily_summary(summary_data):
    """
    Appends or updates the session record in data/audit/daily_summary.csv
    Columns: date, regime, spy_0945, screened, qualified, orders_placed, capital_committed, cancelled_1130, closed_moc, status
    """
    ensure_directories()
    fieldnames = [
        "date", "macro_regime", "spy_0945", "spy_sma50", "spy_sma200",
        "screened_count", "qualified_count", "orders_placed",
        "capital_committed", "cancelled_cutoff", "closed_moc", "status", "last_updated"
    ]

    date = summary_data.get("date", get_current_date_ny())
    rows = []
    updated = False

    if os.path.exists(SUMMARY_CSV):
        try:
            with open(SUMMARY_CSV, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    if r.get("date") == date:
                        # Merge updates into existing record
                        r.update({k: str(v) for k, v in summary_data.items()})
                        r["last_updated"] = datetime.now(EASTERN_TZ).strftime("%H:%M:%S")
                        rows.append(r)
                        updated = True
                    else:
                        rows.append(r)
        except Exception as e:
            logging.getLogger("DualRegime.Audit").error(f"Error reading {SUMMARY_CSV}: {e}")

    if not updated:
        new_row = {k: "" for k in fieldnames}
        new_row.update({k: str(v) for k, v in summary_data.items()})
        new_row["date"] = date
        new_row["last_updated"] = datetime.now(EASTERN_TZ).strftime("%H:%M:%S")
        rows.append(new_row)

    try:
        with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        logging.getLogger("DualRegime.Audit").error(f"Failed to write daily summary CSV: {e}")

def get_daily_log_content(date_str=None):
    if not date_str:
        date_str = get_current_date_ny()
    log_file = os.path.join(LOGS_DIR, f"{date_str}.log")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            return f.read()
    return None

def get_daily_events(date_str=None):
    if not date_str:
        date_str = get_current_date_ny()
    events_file = os.path.join(EVENTS_DIR, f"{date_str}.jsonl")
    events = []
    if os.path.exists(events_file):
        with open(events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    return events

def show_audit_report(date_str=None, show_summary=False):
    """
    Interactive CLI renderer for rapid behavior and outcome auditing
    """
    print("=" * 80)
    print(" STRATEGY #3: QUANTITATIVE AUDIT & EXECUTION LEDGER ")
    print("=" * 80)

    if show_summary:
        if not os.path.exists(SUMMARY_CSV):
            print("No historical daily summary records found in data/audit/daily_summary.csv")
            return
        print("\n--- HISTORICAL TRADING SESSION SUMMARIES ---")
        with open(SUMMARY_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header_fmt = "{:<12} | {:<8} | {:<8} | {:<8} | {:<9} | {:<7} | {:<12} | {:<10}"
            print(header_fmt.format("Date", "Regime", "SPY 9:45", "Screened", "Qualified", "Orders", "Capital", "Status"))
            print("-" * 88)
            for r in reader:
                print(header_fmt.format(
                    r.get("date", ""),
                    r.get("macro_regime", ""),
                    f"${float(r.get('spy_0945', 0)):.2f}" if r.get('spy_0945') else "-",
                    r.get("screened_count", ""),
                    r.get("qualified_count", ""),
                    r.get("orders_placed", ""),
                    f"${float(r.get('capital_committed', 0)):,.2f}" if r.get('capital_committed') else "$0.00",
                    r.get("status", "")
                ))
        print("=" * 80)
        return

    if not date_str:
        date_str = get_current_date_ny()

    events = get_daily_events(date_str)
    log_content = get_daily_log_content(date_str)

    print(f"Audit Target Date: {date_str} (America/New_York)")
    print(f"Total Structured Events Logged: {len(events)}")
    print("-" * 80)

    if events:
        print("\n[CHRONOLOGICAL TIMELINE OF STRATEGY DECISIONS]")
        for i, ev in enumerate(events, 1):
            ts = ev.get("timestamp_ny", "")
            e_type = ev.get("event_type", "")
            p = ev.get("payload", {})

            if e_type == "WARMUP_INIT":
                print(f"  {ts} | [WARMUP]  Runner initialized at {p.get('boot_time')}. Pre-fetching universe metrics...")
            elif e_type == "COUNTDOWN_SYNC":
                print(f"  {ts} | [SYNC]    Reached target execution time {p.get('target')}. Drift: {p.get('drift_ms', 0):+.2f} ms")
            elif e_type == "SCAN_COMPLETE":
                print(f"  {ts} | [SCAN]    Screened {p.get('screened_count')} assets. Macro Regime: {p.get('macro_regime')} (SPY: ${p.get('spy_price', 0):.2f})")
                print(f"         Qualified Candidates: {p.get('qualified_count')}")
                candidates = p.get("qualified_candidates", [])
                for c in candidates[:10]:
                    print(f"           -> #{c.get('rank')} {c.get('symbol'):<5} ({c.get('direction')}) @ Stop ${c.get('entry_stop', 0):.2f} | Gap: {c.get('gap_pct', 0)*100:+.2f}% | RVOL: {c.get('rvol15', 0):.2f}x | ATR: {c.get('atr_pct', 0)*100:.2f}%")
                if len(candidates) > 10:
                    print(f"           ... and {len(candidates) - 10} more candidates.")
            elif e_type == "ORDER_BATCH_COMPLETE":
                print(f"  {ts} | [BATCH]   Submitted {p.get('orders_placed')} orders. Capital Committed: ${p.get('capital_committed', 0):,.2f} | Remaining Cash: ${p.get('remaining_cash', 0):,.2f}")
            elif e_type == "ORDER_SUBMITTED":
                print(f"  {ts} | [ORDER]   #{p.get('index')} {p.get('direction')} 1 share {p.get('symbol')} @ Stop ${p.get('stop_price', 0):.2f} (SL: ${p.get('sl', 0):.2f}, TP: ${p.get('tp', 0):.2f}) | ID: {p.get('order_id')}")
            elif e_type == "ORDER_SKIPPED":
                print(f"  {ts} | [SKIP]    {p.get('symbol')} @ ${p.get('price', 0):.2f} - Reason: {p.get('reason')}")
            elif e_type == "CUTOFF_1130":
                print(f"  {ts} | [CUTOFF]  11:30 AM Cutoff: Cancelled {p.get('cancelled_count')} unfilled resting entry orders.")
            elif e_type == "MOC_LIQUIDATION":
                print(f"  {ts} | [MOC]     15:55 PM MOC: Liquidated {p.get('closed_count')} open positions. Account is 100% Cash.")
            else:
                print(f"  {ts} | [EVENT]   {e_type}: {json.dumps(p)}")
    else:
        print(f"No structured events recorded for {date_str}.")

    if log_content:
        print("\n" + "-" * 80)
        print(f"Log File Location: {os.path.join(LOGS_DIR, f'{date_str}.log')}")
        print(f"Total Log Lines: {len(log_content.splitlines())}")
        print("Tail of Daily Log (last 15 lines):")
        for line in log_content.splitlines()[-15:]:
            print(f"  {line}")
    else:
        print(f"No raw log file found for {date_str}.")

    print("=" * 80)
