import pandas as pd

def check_consecutive(series, ema, date, bars=2, above=True):
    idx = series.index.get_loc(date)
    closes = series.iloc[idx-bars:idx]['close']
    emas = ema.iloc[idx-bars:idx]
    if above:
        result = all(closes > emas)
    else:
        result = all(closes < emas)
    return result

def should_open_trade(df_weekly, df_daily, date):
    """
    Entry rules:
      - Weekly close above WEMA50
      - Two consecutive weekly closes above WEMA8
      - Daily close above DEMA50 and DEMA100
      - If weekly condition met but daily not yet above 50/100, wait until it is
    """
    try:
        weekly_ok = (df_weekly.loc[date, 'close'] > df_weekly.loc[date, 'EMA50']) and \
                    check_consecutive(df_weekly, df_weekly['EMA8'], date, 2, above=True)

        daily_ok = (df_daily.loc[date, 'close'] > df_daily.loc[date, 'EMA50']) and \
                   (df_daily.loc[date, 'close'] > df_daily.loc[date, 'EMA100'])

        return weekly_ok and daily_ok
    except KeyError:
        return False

def should_close_trade(df_daily, date):
    """
    Exit rule:
      - Daily close below DEMA50
    """
    try:
        return df_daily.loc[date, 'close'] < df_daily.loc[date, 'EMA50']
    except KeyError:
        return False

def get_stop_loss(df_daily, date, buffer_points=5):
    """
    Hard stop loss just under daily EMA100
    """
    try:
        return df_daily.loc[date, 'EMA100'] - buffer_points
    except KeyError:
        return None

def position_size(account_value, entry_price):
    """
    £ per point = account_value / entry_price
    """
    return account_value / entry_price if entry_price > 0 else 0

def can_reenter(df_weekly, df_daily, date, big_move_done=False):
    """
    Re-entry rules:
      - Daily has 2 closes above DEMA50
      - No double weekly close below WEMA8 since last entry
      - Not locked out by 1000pt big move
    """
    try:
        daily_reentry = check_consecutive(df_daily, df_daily['EMA50'], date, 2, above=True)
        weekly_block = check_consecutive(df_weekly, df_weekly['EMA8'], date, 2, above=False)
        return daily_reentry and (not weekly_block) and (not big_move_done)
    except KeyError:
        return False