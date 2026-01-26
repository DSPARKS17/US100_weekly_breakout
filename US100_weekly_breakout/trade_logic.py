import pandas as pd

def check_consecutive(df, ema_series, bars=2, above=True):
    """
    Check if the last `bars` closes are consecutively above or below an EMA.
    Returns True/False (boolean).
    """
    if len(df) < bars:
        return False

    closes = df['close'].iloc[-bars:].values
    emas = ema_series.iloc[-bars:].values

    if above:
        return (closes > emas).all()
    else:
        return (closes < emas).all()


def should_open_trade(df_weekly, df_daily):
    try:
        weekly_close = float(df_weekly['close'].iloc[-1])
        weekly_ema_50 = float(df_weekly['EMA50'].iloc[-1])
        weekly_ema_8 = df_weekly['EMA8']

        daily_close = float(df_daily['close'].iloc[-1])
        daily_ema_50 = float(df_daily['EMA50'].iloc[-1])
        daily_ema_100 = float(df_daily['EMA100'].iloc[-1])

        weekly_ok = weekly_close > weekly_ema_50 and check_consecutive(df_weekly, weekly_ema_8, bars=2, above=True)
        daily_ok = daily_close > daily_ema_50 and daily_close > daily_ema_100

        return weekly_ok and daily_ok

    except Exception:
        return False


def should_close_trade(df_daily):
    try:
        daily_close = float(df_daily['close'].iloc[-1])
        daily_ema_50 = float(df_daily['EMA50'].iloc[-1])
        return daily_close < daily_ema_50
    except Exception:
        return False


def get_stop_loss(df_daily, buffer_points=5):
    try:
        return float(df_daily['EMA100'].iloc[-1] - buffer_points)
    except Exception:
        return None


def position_size(account_value, entry_price):
    """
    £ per point = account_value / entry_price
    """
    return float(account_value) / float(entry_price) if entry_price > 0 else 0.0


def can_reenter(df_weekly, df_daily, big_move_done=False):
    try:
        daily_reentry = check_consecutive(df_daily, df_daily['EMA50'], bars=2, above=True)
        weekly_block = check_consecutive(df_weekly, df_weekly['EMA8'], bars=2, above=False)
        return daily_reentry and not weekly_block and not big_move_done
    except Exception:
        return False
