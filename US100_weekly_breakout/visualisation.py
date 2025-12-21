import matplotlib.pyplot as plt
import config

def plot_trades(df, trades, title=None):
    """
    Plot OHLC close price, EMAs, and trade entry/exit points.

    Parameters:
        df (pd.DataFrame): Must contain 'close', EMA columns (EMA_SHORT, EMA_MEDIUM, EMA_LONG)
        trades (list of dicts or objects): Each trade must have 'entry_date', 'entry_price', 'exit_date', 'exit_price'
        title (str, optional): Plot title
    """
    plt.figure(figsize=config.PLOT_SIZE)
    
    # Plot Close price
    plt.plot(df.index, df['close'], label='Close Price', color='blue')
    
    # Plot EMAs
    plt.plot(df.index, df[f'EMA{config.EMA_SHORT}'], label=f'EMA {config.EMA_SHORT}', linestyle='--', color='orange')
    plt.plot(df.index, df[f'EMA{config.EMA_MEDIUM}'], label=f'EMA {config.EMA_MEDIUM}', linestyle='--', color='green')
    plt.plot(df.index, df[f'EMA{config.EMA_LONG}'], label=f'EMA {config.EMA_LONG}', linestyle='--', color='red')
    
    # Plot trade entry/exit points
    for trade in trades:
        plt.scatter(trade['entry_date'], trade['entry_price'], marker='^', color='green', s=100, label='Entry')
        if trade['exit_date'] and trade['exit_price']:
            plt.scatter(trade['exit_date'], trade['exit_price'], marker='v', color='red', s=100, label='Exit')
    
    # Avoid duplicate labels
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    
    plt.legend(by_label.values(), by_label.keys())
    plt.title(title or f"{config.SYMBOL} Trading Signals")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(config.PLOT_GRID)
    plt.tight_layout()
    plt.show()


def plot_cumulative_pnl(trades, title=None):
    """
    Plot cumulative PnL from executed trades.
    trades: list of trade dicts with 'pnl' key
    """
    cumulative_pnl = []
    total = 0
    for t in trades:
        total += t['pnl']
        cumulative_pnl.append(total)
    
    plt.figure(figsize=config.PLOT_SIZE)
    plt.plot(range(len(cumulative_pnl)), cumulative_pnl, marker='o', color='purple')
    plt.title(title or f"{config.SYMBOL} Cumulative PnL")
    plt.xlabel("Trade Number")
    plt.ylabel("Cumulative PnL (£)")
    plt.grid(config.PLOT_GRID)
    plt.tight_layout()
    plt.show()