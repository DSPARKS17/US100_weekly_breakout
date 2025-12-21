### backtest.py
import pandas as pd
from indicators import compute_ema, compute_volatility
from trade_logic import should_open_trade, should_close_trade
from utils import load_data, calculate_position_size, Trade
from visualisation import plot_signals
import config

# ---------------------------
# Settings
# ---------------------------
ACCOUNT_BALANCE = config.ACCOUNT_VALUE
RISK_PERCENTAGE = config.MAX_RISK_PERCENT

# ---------------------------
# Load historical data
# ---------------------------
df_weekly, df_daily, df_4h = load_data(config.SYMBOL)

# ---------------------------
# Calculate EMAs
# ---------------------------
df_weekly['EMA8'] = compute_ema(df_weekly['close'], config.EMA_SHORT)
df_weekly['EMA50'] = compute_ema(df_weekly['close'], config.EMA_MEDIUM)
df_weekly['EMA100'] = compute_ema(df_weekly['close'], config.EMA_LONG)

df_daily['EMA8'] = compute_ema(df_daily['close'], config.EMA_SHORT)
df_daily['EMA50'] = compute_ema(df_daily['close'], config.EMA_MEDIUM)
df_daily['EMA100'] = compute_ema(df_daily['close'], config.EMA_LONG)

# ---------------------------
# Compute volatility
# ---------------------------
weekly_volatility = compute_volatility(df_weekly)

# ---------------------------
# Backtesting loop
# ---------------------------
account_balance = ACCOUNT_BALANCE
open_trade = None
trade_log = []
signals = []

# Start after enough data for EMAs
for date in df_daily.index[max(config.EMA_LONG, config.CONSECUTIVE_BARS):]:
    daily_close = df_daily.loc[date, 'close']
    daily_low = df_daily.loc[date, 'low']

    # Manage open trade
    if open_trade:
        if should_close_trade(df_daily, date) or open_trade.hit_stop(daily_low):
            open_trade.close(daily_close, date)
            account_balance += open_trade.profit
            trade_log.append(open_trade)
            signals.append({"date": date, "type": "exit"})
            open_trade = None
        # Optional: Implement reduce logic here if needed
    else:
        if should_open_trade(df_weekly, df_daily, date):
            vol = weekly_volatility.get(date, weekly_volatility.iloc[-1])
            stop_distance = vol * 2
            size = calculate_position_size(account_balance, stop_distance, RISK_PERCENTAGE)
            entry_price = daily_close
            stop_loss = entry_price - stop_distance
            open_trade = Trade(entry_price, stop_loss, size, date)
            signals.append({"date": date, "type": "entry"})

# ---------------------------
# Output results
# ---------------------------
for t in trade_log:
    print(t)

print(f"\nFinal Balance: £{account_balance:.2f}")

# ---------------------------
# Plot entries/exits
# ---------------------------
plot_signals(df_daily, signals)
