import pandas as pd
import config


def check_consecutive(df, ema_series, bars=2, above=True):
    """
    Check if the last `bars` closes are consecutively above or below an EMA.
    Uses the most recent completed bars only.
    """
    if len(df) < bars + 1:
        return False

    closes = df['close'].iloc[-bars-1:-1]
    emas = ema_series.iloc[-bars-1:-1]

    if above:
        return (closes > emas).all()
    else:
        return (closes < emas).all()


def should_open_trade(df_weekly, df_daily, date=None):
    """
    Entry rules (evaluated once per day on latest data):
      - Weekly close above WEMA50
      - Two consecutive weekly closes above WEMA8
      - Daily close above DEMA50 and DEMA100
    """
    try:
        # Latest completed bars
        weekly_close = df_weekly['close'].iloc[-1]
        weekly_ema_50 = df_weekly['EMA50'].iloc[-1]

        daily_close = df_daily['close'].iloc[-1]
        daily_ema_50 = df_daily['EMA50'].iloc[-1]
        daily_ema_100 = df_daily['EMA100'].iloc[-1]

        weekly_ok = (
            weekly_close > weekly_ema_50
            and check_consecutive(df_weekly, df_weekly['EMA8'], bars=2, above=True)
        )

        daily_ok = (
            daily_close > daily_ema_50
            and daily_close > daily_ema_100
        )

        return bool(weekly_ok and daily_ok)

    except Exception:
        return False


def should_close_trade(df_daily, date=None):
    """
    Exit rule:
      - Daily close below DEMA50
    """
    try:
        daily_close = df_daily['close'].iloc[-1]
        daily_ema_50 = df_daily['EMA50'].iloc[-1]

        return bool(daily_close < daily_ema_50)

    except Exception:
        return False


def get_stop_loss(df_daily, buffer_points=5):
    """
    Hard stop loss just under daily EMA100
    """
    try:
        return float(df_daily['EMA100'].iloc[-1] - buffer_points)
    except Exception:
        return None


def position_size(account_value, entry_price):
    """
    £ per point = account_value / entry_price
    """
    return account_value / entry_price if entry_price > 0 else 0


def can_reenter(df_weekly, df_daily, big_move_done=False):
    """
    Re-entry rules:
      - Daily has 2 closes above DEMA50
      - No double weekly close below WEMA8 since last entry
      - Not locked out by big move
    """
    try:
        daily_reentry = check_consecutive(
            df_daily, df_daily['EMA50'], bars=2, above=True
        )

        weekly_block = check_consecutive(
            df_weekly, df_weekly['EMA8'], bars=2, above=False
        )

        return bool(daily_reentry and not weekly_block and not big_move_done)

    except Exception:
        return False
