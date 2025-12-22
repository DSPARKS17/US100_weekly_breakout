# daily_runner.py
from datetime import datetime
import os
import config
from ig_data_loader import IGDataLoader
from notification import send_whatsapp_message
from logger import log_info, log_error

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
            "TWILIO_TO"
        ]
        for s in secrets_list:
            value = os.getenv(s)
            log_info(f"Secret {s}: {'FOUND' if value else 'MISSING'}")

        # Initialize IGDataLoader
        loader = IGDataLoader()
        daily_df = loader.fetch_latest_prices(numpoints=2)  # fetch last 2 days
        log_info("Data loaded successfully.")

        # Take the previous completed day
        last_day = daily_df.iloc[-2]

        # Convert to floats explicitly
        open_price  = float(last_day['open'])
        high_price  = float(last_day['high'])
        low_price   = float(last_day['low'])
        close_price = float(last_day['close'])

        # Build message
        message = (
            f"📊 {config.SYMBOL} Daily Summary ({datetime.now().strftime('%Y-%m-%d')})\n"
            f"Open : {open_price:.1f}\n"
            f"High : {high_price:.1f}\n"
            f"Low  : {low_price:.1f}\n"
            f"Close: {close_price:.1f}"
        )

        # Send WhatsApp message
        send_whatsapp_message(message)
        log_info("WhatsApp message sent successfully.")

    except Exception as e:
        log_error(f"Error in daily runner: {e}")

if __name__ == "__main__":
    main()




