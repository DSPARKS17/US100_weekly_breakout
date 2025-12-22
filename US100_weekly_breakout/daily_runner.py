# daily_runner.py
from datetime import datetime
import os

import config
from ig_data_loader import IGDataLoader
from notification import send_whatsapp_message
from logger import log_info, log_error


def _scalar(value):
    """
    Safely extract a scalar from pandas Series / numpy types.
    Avoids FutureWarning and future breakage.
    """
    try:
        return value.item()
    except AttributeError:
        return value


def main():
    try:
        # --- CI sanity check (GitHub Actions only) ---
        if os.getenv("GITHUB_ACTIONS") == "true":
            log_info("Running inside GitHub Actions")
            log_info(
                f"Env check | "
                f"TWILIO_ACCOUNT_SID={bool(os.getenv('TWILIO_ACCOUNT_SID'))}, "
                f"TWILIO_AUTH_TOKEN={bool(os.getenv('TWILIO_AUTH_TOKEN'))}, "
                f"TWILIO_WHATSAPP_FROM={bool(os.getenv('TWILIO_WHATSAPP_FROM'))}, "
                f"TWILIO_WHATSAPP_TO={bool(os.getenv('TWILIO_WHATSAPP_TO'))}"
            )

        # Initialize IGDataLoader
        loader = IGDataLoader()
        daily_df = loader.fetch_latest_prices(numpoints=2)  # last 2 days
        log_info("Data loaded successfully.")

        # Previous completed day
        last_day = daily_df.iloc[-2]

        # Safe scalar extraction
        open_price  = _scalar(last_day["open"])
        high_price  = _scalar(last_day["high"])
        low_price   = _scalar(last_day["low"])
        close_price = _scalar(last_day["close"])

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




