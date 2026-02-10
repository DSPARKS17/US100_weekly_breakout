from datetime import datetime
import os
import pandas as pd
import config
from ig_data_loader import IGDataLoader
from notification import send_whatsapp_message
from telegram_notification import send_telegram_message
from logger import log_info, log_error
from trade_logic import (
    should_open_trade,
    should_close_trade,
    get_stop_loss,
    position_size,
    can_reenter,
    find_weekly_trend_reversal
)
from trade_state import load_state, save_state

FALLBACK_ACCOUNT_VALUE = 13000


def to_week_commencing(ts):
    ts = pd.to_datetime(ts)

    # 🔑 normalize timezone (fixes UTC vs naive comparison errors)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)

    return (ts - pd.Timedelta(days=ts.weekday())).date()


def main():
    try:
        # ---------------------------
        # Debug: check secrets
        # ---------------------------
        secrets_list = [
            "IG_USERNAME", "IG_PASSWORD", "IG_API_KEY",
            "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM", "TWILIO_TO",
            "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"
        ]
        for s in secrets_list:
            value = os.getenv(s)
            log_info(f"Secret {s}: {'FOUND' if value else 'MISSING'}")

        # ---------------------------
        # Load data
        # ---------------------------
        loader = IGDataLoader()

        DAILY_BARS = 250
        WEEKLY_BARS = 200

        daily_df = loader.fetch_daily_prices(numpoints=DAILY_BARS)
        weekly_df = loader.fetch_weekly_prices(numpoints=WEEKLY_BARS)

        if len(daily_df) < 120:
            raise ValueError(f"Insufficient daily bars returned: {len(daily_df)}")
        if len(weekly_df) < 60:
            raise ValueError(f"Insufficient weekly bars returned: {len(weekly_df)}")

        log_info("Price data loaded.")

        # ---------------------------
        # Fetch account balance
        # ---------------------------
        account_value = loader.fetch_account_balance() or FALLBACK_ACCOUNT_VALUE
        log_info(f"Using account value: £{account_value:.2f}")

        # ---------------------------
        # Calculate EMAs
        # ---------------------------
        daily_df["EMA50"] = daily_df["close"].ewm(span=50, adjust=False).mean()
        daily_df["EMA100"] = daily_df["close"].ewm(span=100, adjust=False).mean()
        daily_df["EMA8"] = daily_df["close"].ewm(span=8, adjust=False).mean()

        weekly_df["EMA50"] = weekly_df["close"].ewm(span=50, adjust=False).mean()
        weekly_df["EMA8"] = weekly_df["close"].ewm(span=8, adjust=False).mean()

        # ---------------------------
        # Latest daily values (last fully closed bar)
        # ---------------------------
        last_daily = daily_df.iloc[-2]

        close_price = float(last_daily["close"].item())
        ema50 = float(last_daily["EMA50"].item())
        ema100 = float(last_daily["EMA100"].item())
        ema8 = float(last_daily["EMA8"].item())

        # ---------------------------
        # Latest weekly values (completed weeks only)
        # ---------------------------
        last_weekly = weekly_df.iloc[-2]
        prev_weekly = weekly_df.iloc[-3]

        weekly_close_last = float(last_weekly["close"].item())
        weekly_close_prev = float(prev_weekly["close"].item())
        weekly_ema50 = float(last_weekly["EMA50"].item())
        weekly_ema8_last = float(last_weekly["EMA8"].item())
        weekly_ema8_prev = float(prev_weekly["EMA8"].item())

        wc_prev = to_week_commencing(prev_weekly.name)
        wc_last = to_week_commencing(last_weekly.name)
        weekly_dates_str = f"wc {wc_prev} / wc {wc_last}"

        # ---------------------------
        # Weekly trend (reversal logic)
        # ---------------------------
        weekly_trend_valid, weekly_valid_since = find_weekly_trend_reversal(weekly_df)

        if weekly_trend_valid and weekly_valid_since is not None:
            wc_valid_since = to_week_commencing(weekly_valid_since)
            weekly_trend_str = f"VALID as of wc {wc_valid_since}"
        else:
            weekly_trend_str = "INVALID"

        # ---------------------------
        # Load trade state
        # ---------------------------
        state = load_state()
        big_move_done = state.get("big_move_done", False)

        # ---------------------------
        # Suggested position size
        # ---------------------------
        suggested_size = position_size(account_value, close_price)
        stop_loss = get_stop_loss(last_daily)

        # ---------------------------
        # Compose message
        # ---------------------------
        entry_allowed = should_open_trade(weekly_df, daily_df)
        reentry_allowed = can_reenter(weekly_df, daily_df, big_move_done)

        action_msg = (
            f"Trade Status:\n🔴 NOT IN TRADE\n\n"
            f"Entry Conditions:\n"
            f"Weekly trend: {weekly_trend_str}\n"
            f"Daily trend: {'VALID' if close_price > ema50 and close_price > ema100 else 'INVALID'}\n"
            f"Re-entry allowed: {'YES' if reentry_allowed else 'NO'}\n"
            f"Big move lockout: {'YES' if big_move_done else 'NO'}\n\n"
            f"If opened today:\nSuggested size: £{suggested_size:.2f} / point\n"
            f"Stop loss: {stop_loss:.2f} (Daily EMA100)\n\n"
            f"📌 Action:\n➡️ {'Consider OPENING a long position' if entry_allowed else 'Do nothing'}"
        )

        # ---------------------------
        # Build final message
        # ---------------------------
        message = "\n".join([
            f"📊 {config.SYMBOL} Daily Strategy Update",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}\n",
            f"Account Value: £{account_value:.2f}\n",
            "Daily:",
            f"Close: {close_price:.2f}",
            f"EMA50: {ema50:.2f}",
            f"EMA100: {ema100:.2f}",
            f"EMA8: {ema8:.2f}\n",
            "Weekly:",
            f"Close above EMA50: {weekly_close_last:.2f} vs EMA50 {weekly_ema50:.2f}",
            f"2 consecutive closes above EMA8 ({weekly_dates_str}): "
            f"{weekly_close_prev:.2f} / {weekly_close_last:.2f} vs EMA8: "
            f"{weekly_ema8_prev:.2f} / {weekly_ema8_last:.2f}\n",
            action_msg
        ])

        # ---------------------------
        # Send messages
        # ---------------------------
        send_telegram_message(message)
        send_whatsapp_message(message)
        log_info("Daily strategy update sent successfully.")

        save_state(state)

    except Exception as e:
        log_error(f"Error in daily runner: {e}")


if __name__ == "__main__":
    main()
