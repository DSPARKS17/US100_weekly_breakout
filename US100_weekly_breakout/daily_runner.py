from datetime import datetime
import pandas as pd

# Custom modules
import config
from data_loader import load_data
from indicators import compute_ema
from trade_logic import should_open_trade, should_close_trade
from trade_state import load_state, save_state, open_position, close_position
from notification import send_email
from logger import log_info, log_debug, log_warning, log_error
from visualization import plot_trades, plot_cumulative_pnl

def main():
    try:
        # ---------------------------
        # Load Data
        # ---------------------------
        weekly_df, daily_df, _ = load_data(config.SYMBOL)
        log_info("Data loaded successfully.")

        # ---------------------------
        # Compute EMAs
        # ---------------------------
        for period in [config.EMA_SHORT, config.EMA_MEDIUM, config.EMA_LONG]:
            daily_df[f'EMA{period}'] = compute_ema(daily_df['close'], period)
            weekly_df[f'EMA{period}'] = compute_ema(weekly_df['close'], period)
        log_debug("EMAs computed.")

        # ---------------------------
        # Load Trade State
        # ---------------------------
        state = load_state()
        log_info(f"Current position: {state.get('position')}")

        # ---------------------------
        # Trading Logic
        # ---------------------------
        today = daily_df.index[-1]
        price = daily_df['close'].iloc[-1]

        # Check if we should open a new trade
        if should_open_trade(weekly_df, daily_df, today):
            # Compute size & stop
            size = config.ACCOUNT_VALUE / price  # Simple example
            stop = daily_df[f'EMA{config.EMA_LONG}'].iloc[-1] * 0.99  # Just under EMA100
            open_position(state, today.strftime('%Y-%m-%d'), price, size, stop)
            log_info(f"Trade opened at {price} with size {size} and stop {stop}")
            send_email("📈 Trade Opened", f"Date: {today}\nPrice: {price}\nSize: {size}\nStop: {stop}")

        # Check if we should close the trade
        elif should_close_trade(daily_df, today):
            close_price = daily_df['close'].iloc[-1]
            close_position(state, today.strftime('%Y-%m-%d'), close_price)
            log_info(f"Trade closed at {close_price}")
            send_email("💸 Trade Closed", f"Date: {today}\nPrice: {close_price}")

        # ---------------------------
        # Save Trade State
        # ---------------------------
        save_state(state)

        # ---------------------------
        # Optional Visualization
        # ---------------------------
        if config.PLOT_AFTER_RUN:
            plot_trades(daily_df, state.get('history', []))
            plot_cumulative_pnl(state.get('history', []))

    except Exception as e:
        log_error(f"Error in daily runner: {e}")

# Entry point
if __name__ == "__main__":
    main()
