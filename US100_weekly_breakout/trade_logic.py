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


def find_weekly_trend_reversal(df_weekly):
    """
    Stateful weekly trend logic.

    Returns:
        (is_valid: bool, valid_since: Timestamp | None)
    """
    closes = df_weekly['close']
    ema8 = df_weekly['EMA8']
    dates = df_weekly.index

    above = closes > ema8
    below = closes < ema8

    valid = False
    valid_since = None
    below_streak = 0
    seen_two_below = False

    for i in range(len(df_weekly)):
        if below.iloc[i]:
            below_streak += 1
        else:
            below_streak = 0

        # Mark that we've had a bearish regime
        if below_streak >= 2:
            seen_two_below = True

        # Detect reversal ONLY after bearish regime
        if (
            seen_two_below
            and i >= 1
            and above.iloc[i]
            and above.iloc[i - 1]
            and not valid
        ):
            valid = True
            valid_since = dates[i]  # use the second consecutive close above EMA8
            below_streak = 0
            continue

        # If valid, watch for invalidation
        if valid and below_streak >= 2:
            valid = False
            valid_since = None
            seen_two_below = True  # reset for next cycle

    return valid, valid_since


def should_open_trade(df_weekly, df_daily):
    try:
        weekly_valid, _ = find_weekly_trend_reversal(df_weekly)

        daily_close = float(df_daily['close'].iloc[-2])
        daily_ema50 = float(df_daily['EMA50'].iloc[-2])
        daily_ema100 = float(df_daily['EMA100'].iloc[-2])

        daily_ok = daily_close > daily_ema50 and daily_close > daily_ema100

        return weekly_valid and daily_ok

    except Exception:
        return False


def should_close_trade(df_daily):
    try:
        daily_close = float(df_daily['close'].iloc[-2])
        daily_ema50 = float(df_daily['EMA50'].iloc[-2])
        return daily_close < daily_ema50
    except Exception:
        return False


def get_stop_loss(last_closed_daily, buffer_points=5):
    try:
        ema100 = float(last_closed_daily['EMA100'])
        return ema100 - buffer_points
    except Exception:
        return None


def position_size(account_value, entry_price):
    return float(account_value) / float(entry_price) if entry_price > 0 else 0.0


def can_reenter(df_weekly, df_daily, big_move_done=False):
    try:
        daily_reentry = check_consecutive(df_daily, df_daily['EMA50'], bars=2, above=True)
        weekly_block = check_consecutive(df_weekly, df_weekly['EMA8'], bars=2, above=False)
        return daily_reentry and not weekly_block and not big_move_done
    except Exception:
        return False
