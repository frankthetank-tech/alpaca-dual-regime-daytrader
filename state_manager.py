"""
Strategy #3: Atomic State Manager
Persists daily macro regime, selected candidate, order IDs, and trading states
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger("DualRegime.State")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
STATE_FILE = os.path.join(DATA_DIR, "state.json")

def get_default_state():
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "macro_regime": "NEUTRAL",
        "spy_0945": 0.0,
        "spy_sma50": 0.0,
        "spy_sma200": 0.0,
        "selected_candidate": None,
        "direction": None,
        "entry_stop_price": 0.0,
        "stop_loss_price": 0.0,
        "take_profit_price": 0.0,
        "order_status": "IDLE", # IDLE, SUBMITTED, FILLED, EXPIRED, CLOSED
        "order_id": None,
        "last_updated": datetime.now().isoformat()
    }

def load_state():
    if not os.path.exists(STATE_FILE):
        return get_default_state()
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read {STATE_FILE}: {e}")
        return get_default_state()

def save_state(state):
    os.makedirs(DATA_DIR, exist_ok=True)
    state["last_updated"] = datetime.now().isoformat()
    temp_file = STATE_FILE + ".tmp"
    try:
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)
        logger.info(f"State saved successfully to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to write state: {e}")
