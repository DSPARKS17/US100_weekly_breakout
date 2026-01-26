import json
import os

STATE_FILE = 'trade_state.json'

def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "position": None,
            "history": [],
            "first_entry_price": None,
            "big_move_done": False,
            "window_active": False,
            "weekly_block": False
        }
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def open_position(state, date, price, size, stop):
    if state.get("first_entry_price") is None:
        state["first_entry_price"] = price

    state['position'] = {
        'entry_date': date,
        'entry_price': price,
        'size': size,
        'stop_loss': stop
    }

    return {
        "action": "OPEN",
        "entry_price": price,
        "size": size,
        "stop_loss": stop
    }

def close_position(state, date, price, big_move_threshold=1000):
    if not state['position']:
        return None

    entry = state['position']
    pnl = (price - entry['entry_price']) * entry['size']

    state['history'].append({
        'entry_date': entry['entry_date'],
        'entry_price': entry['entry_price'],
        'exit_date': date,
        'exit_price': price,
        'size': entry['size'],
        'pnl': pnl
    })

    if state.get("first_entry_price") is not None:
        move = price - state["first_entry_price"]
        if move >= big_move_threshold:
            state["big_move_done"] = True

    state['position'] = None

    return {
        "action": "CLOSE",
        "exit_price": price,
        "pnl": pnl
    }

def reset_window(state):
    state["first_entry_price"] = None
    state["big_move_done"] = False
    state["window_active"] = True
    state["weekly_block"] = False

def end_window(state):
    state["window_active"] = False
    state["weekly_block"] = True

