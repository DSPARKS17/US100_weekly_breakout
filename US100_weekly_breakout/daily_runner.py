# daily_runner.py
from datetime import datetime
import os
import pandas as pd
import config
from ig_data_loader import IGDataLoader
from notification import send_whatsapp_message
from telegram_notification import send_telegram_message
from logger import log_info, log_error
from trade_logic import should_open_trade, should_close_trade

# ---------------------------
# Helper functions
# ---------------------------
def infer_trade_state(df_weekly, df_daily):
    """
    Infer current trade state (in_trade: True/False) based on historical data.
    Iterates through historical daily and weekly closes.
    """
    in_trade = False
    # Ensure data is sorted oldest -> newest
    df_daily = df_daily.reset_index(drop=True)
    df_weekly = df_weekly.reset_index(drop=True)

    for i in range(len(df_daily)):
        daily_slice = df_daily.iloc[:i+1]
        weekly_slice = df_weekly.iloc[:i+1]

        if not in_trade and should_open_trade(weekly_slice, daily_slice):
            in_trade = True
        elif in_trade and should_close_trade(daily_slice):
            in_trade = False
    return in_trade

# ---------------------------
# Main runner
# ---------------------------
def main():
    try:
        # ---------------------------
        # DEBUG: Check if secrets are detected
        # ---------------------------
        secrets_list = [
            "IG_USERNAME",
            "IG_PASSWORD",
            "IG_API_KEY",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_FROM",
            "TWILIO_TO",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID"
        ]
        for s in secrets_list:
            value = os.getenv(s)
            log_info(f"Secret {s}: {'FOUND' if value else 'MISSING'}")

        # ---------------------------
        # Load data
        # ---------------------------
        loader = IGDataLoader()
        daily_df = loader.fetch_latest_prices(numpoints=50)  # fetch last 50 daily bars
        weekly_df = loader.fetch_latest_prices(numpoints=50)  # replace with actual weekly fetch if available
        log_info("Data loaded successfully.")

        # Take the latest completed day
        last_day = daily_df.iloc[-2]

        # Convert to floats explicitly
        open_price  = float(last_day['open'])
        high_price  = float(last_day['high'])
        low_price   = float(last_day['low'])
        close_price = float(last_day['close'])

        # Calculate 8EMA on daily close
        daily_df['EMA8'] = daily_df['close'].ewm(span=8, adjust=False).mean()
        ema8 = daily_df['EMA8'].iloc[-2]

        # Infer current trade state
        in_trade = infer_trade_state(weekly_df, daily_df)

        # Decide action message
        if in_trade:
            action_msg = "📈 Currently in trade: remain open or close if exit conditions met."
        else:
            action_msg = "📉 Currently not in trade: consider opening if entry conditions met."

        # Build message
        message = (
            f"📊 {config.SYMBOL} Daily Summary ({datetime.now().strftime('%Y-%m-%d')})\n"
            f"Open : {open_price:.2f}\n"
            f"High : {high_price:.2f}\n"
            f"Low  : {low_price:.2f}\n"
            f"Close: {close_price:.2f}\n"
            f"8EMA : {ema8:.2f}\n\n"
            f"{action_msg}"
        )

        # Send telegram/WhatsApp message
        send_telegram_message(message)
        send_whatsapp_message(message)
        log_info("WhatsApp message sent successfully.")

    except Exception as e:
        log_error(f"Error in daily runner: {e}")

if __name__ == "__main__":
    main()




