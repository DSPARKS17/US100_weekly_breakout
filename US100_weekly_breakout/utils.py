import pandas as pd
import os

# ---------------------------
# Trade Class
# ---------------------------
class Trade:
    def __init__(self, entry_price, stop_loss, size, entry_time):
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.size = size
        self.entry_time = pd.to_datetime(entry_time)
        self.exit_price = None
        self.exit_time = None
        self.profit = 0

    def close(self, exit_price, time):
        self.exit_price = exit_price
        self.exit_time = pd.to_datetime(time)
        self.profit = (self.exit_price - self.entry_price) * self.size

    def reduce(self, price, time):
        self.size /= 2
        print(f"Position reduced at {price} on {time}")

    def hit_stop(self, price):
        return price <= self.stop_loss

    def is_profitable(self):
        return self.profit > 0

    def duration(self):
        if self.exit_time:
            return (self.exit_time - self.entry_time).days
        return 0

    def __str__(self):
        return f"Trade from {self.entry_time} to {self.exit_time} | Size: £{self.size:.2f} | PnL: £{self.profit:.2f}"


# ---------------------------
# Position Sizing
# ---------------------------
def calculate_position_size(account_value, entry_price, stop_loss, max_risk_percent=0.02):
    """
    Calculate position size based on account risk and stop-loss distance.
    Ensures no more than max_risk_percent of account is risked.
    """
    stop_distance = abs(entry_price - stop_loss)
    if stop_distance == 0:
        raise ValueError("Stop loss cannot equal entry price.")
    risk_amount = account_value * max_risk_percent
    size = risk_amount / stop_distance
    return size


# ---------------------------
# Data Loading
# ---------------------------
def load_data(symbol, data_dir="data"):
    """
    Load OHLCV data for different timeframes (weekly, daily, 4h).
    Assumes CSV files exist in `data_dir` with filenames: SYMBOL_weekly.csv, etc.
    """
    df_weekly = pd.read_csv(os.path.join(data_dir, f"{symbol}_weekly.csv"),
                            index_col='date', parse_dates=True)
    df_daily = pd.read_csv(os.path.join(data_dir, f"{symbol}_daily.csv"),
                           index_col='date', parse_dates=True)
    df_4h = pd.read_csv(os.path.join(data_dir, f"{symbol}_4h.csv"),
                        index_col='date', parse_dates=True)
    return df_weekly, df_daily, df_4h


def add_emas(df, periods=[8, 50, 100]):
    """
    Add EMAs for specified periods to the DataFrame.
    """
    for p in periods:
        df[f'EMA{p}'] = df['close'].ewm(span=p, adjust=False).mean()
    return df


# ---------------------------
# EMA Checks
# ---------------------------
def consecutive_above(df, ema_col, bars=2):
    """
    Returns True if last `bars` closes are all above specified EMA column.
    """
    if len(df) < bars:
        return False
    return all(df['close'].iloc[-bars:] > df[ema_col].iloc[-bars:])


def consecutive_below(df, ema_col, bars=2):
    """
    Returns True if last `bars` closes are all below specified EMA column.
    """
    if len(df) < bars:
        return False
    return all(df['close'].iloc[-bars:] < df[ema_col].iloc[-bars:])


# ---------------------------
# File / Directory Helpers
# ---------------------------
def ensure_data_dir(directory="data"):
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")