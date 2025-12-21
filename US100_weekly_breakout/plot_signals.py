import matplotlib.pyplot as plt
import pandas as pd

def plot_signals(df, signals, stop_buffer=5):
    """
    df must include: 'close', 'EMA8', 'EMA50', 'EMA100'
    signals = list of dicts like:
        {"date": "2022-03-15", "type": "entry"}
        {"date": "2022-05-12", "type": "exit"}
        {"date": "2022-07-01", "type": "window_start"}
        {"date": "2022-08-10", "type": "window_end"}
    """
    plt.figure(figsize=(14, 7))
    
    # Plot price + EMAs
    plt.plot(df['close'], label='Close Price', color='blue')
    plt.plot(df['EMA8'], label='8EMA', color='orange', linestyle='--')
    plt.plot(df['EMA50'], label='50EMA', color='green', linestyle='--')
    plt.plot(df['EMA100'], label='100EMA', color='red', linestyle='--')
    
    # Optional stop line (EMA100 - buffer)
    stop_line = df['EMA100'] - stop_buffer
    plt.plot(stop_line, label='Stop (EMA100-buffer)', color='purple', linestyle=':')
    
    # Extract signal dates
    entries = [s['date'] for s in signals if s['type'] == 'entry']
    exits   = [s['date'] for s in signals if s['type'] == 'exit']
    win_starts = [s['date'] for s in signals if s['type'] == 'window_start']
    win_ends   = [s['date'] for s in signals if s['type'] == 'window_end']
    
    # Map to price
    entry_prices = df.loc[entries]['close'] if entries else []
    exit_prices  = df.loc[exits]['close'] if exits else []
    start_prices = df.loc[win_starts]['close'] if win_starts else []
    end_prices   = df.loc[win_ends]['close'] if win_ends else []
    
    # Scatter markers
    if entries:
        plt.scatter(entries, entry_prices, marker='^', color='green', label='Entry', zorder=5)
    if exits:
        plt.scatter(exits, exit_prices, marker='v', color='red', label='Exit', zorder=5)
    if win_starts:
        plt.scatter(win_starts, start_prices, marker='o', color='cyan', label='Window Start', zorder=5)
    if win_ends:
        plt.scatter(win_ends, end_prices, marker='x', color='black', label='Window End', zorder=5)
    
    plt.title('US100 - Strategy Signals with EMA filters')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()