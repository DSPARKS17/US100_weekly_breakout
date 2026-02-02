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

        # ---------------------------
        # Ensure consistent indexes
        # ---------------------------
        daily_df.index = pd.date_range(end=datetime.now(), periods=len(daily_df), freq='B')
        weekly_df.index = pd.date_range(end=datetime.now(), periods=len(weekly_df), freq='W-FRI')

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
        daily_df['EMA50'] = daily_df['close'].ewm(span=50, adjust=False).mean()
        daily_df['EMA100'] = daily_df['close'].ewm(span=100, adjust=False).mean()
        daily_df['EMA8'] = daily_df['close'].ewm(span=8, adjust=False).mean()

        weekly_df['EMA50'] = weekly_df['close'].ewm(span=50, adjust=False).mean()
        weekly_df['EMA8'] = weekly_df['close'].ewm(span=8, adjust=False).mean()

        # ---------------------------
        # Latest daily values (last fully closed bar)
        # ---------------------------
        last_daily = daily_df.iloc[-2]
        close_price = float(last_daily['close'])
        ema50 = float(last_daily['EMA50'])
        ema100 = float(last_daily['EMA100'])
        ema8 = float(last_daily['EMA8'])

        # ---------------------------
        # Latest weekly values
        # ---------------------------
        last_weekly = weekly_df.iloc[-2]
        prev_weekly = weekly_df.iloc[-3]
        weekly_close_last = float(last_weekly['close'])
        weekly_close_prev = float(prev_weekly['close'])
        weekly_ema50 = float(last_weekly['EMA50'])
        weekly_ema8_last = float(last_weekly['EMA8'])
        weekly_ema8_prev = float(prev_weekly['EMA8'])

        weekly_trend_valid, weekly_valid_since = find_weekly_trend_reversal(weekly_df)
        weekly_trend_str = (
            f"VALID as of {weekly_valid_since.strftime('%Y-%m-%d')}" if weekly_trend_valid else "INVALID"
        )

        # ---------------------------
        # Load trade state
        # ---------------------------
        state = load_state()
        big_move_done = state.get("big_move_done", False)

        # ---------------------------
        # Check open positions via IG
        # ---------------------------
        try:
            positions_df = loader.ig_service.fetch_open_positions()
            in_trade = not positions_df.empty
            if in_trade:
                pos = positions_df.iloc[0]
                entry_price = float(pos['level'])
                stop_level = float(pos['stopLevel']) if pos['stopLevel'] else None
                created_date = pd.to_datetime(pos['createdDate'])
                points_move = close_price - entry_price
        except Exception as e:
            log_error(f"Error fetching open positions: {e}")
            in_trade = False

        # ---------------------------
        # Suggested position size
        # ---------------------------
        suggested_size = position_size(account_value, close_price)
        stop_loss = get_stop_loss(last_daily)

        # ---------------------------
        # Compose message
        # ---------------------------
        if in_trade:
            action_msg = (
                f"Trade Status:\n🟢 IN TRADE\n"
                f"Entry price: {entry_price:.2f}\n"
                f"Stop level: {stop_level if stop_level else 'N/A'}\n"
                f"Entry date: {created_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"Current move: {points_move:+.0f} points\n"
                f"Big move reached: {'YES' if big_move_done else 'NO'}\n"
                f"Position size: £{state['position']['size']:.2f} / point\n\n"
                f"📌 Action:\n➡️ Hold position"
            )
        else:
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
            f"2 consecutive closes above EMA8 ({prev_weekly.name.date()} / {last_weekly.name.date()}): "
            f"{weekly_close_prev:.2f} / {weekly_close_last:.2f} vs EMA8: {weekly_ema8_prev:.2f} / {weekly_ema8_last:.2f}\n",
            action_msg
        ])

        # ---------------------------
        # Send messages
        # ---------------------------
        send_telegram_message(message)
        send_whatsapp_message(message)
        log_info("Daily strategy update sent successfully.")

        # ---------------------------
        # Save trade state
        # ---------------------------
        save_state(state)

    except Exception as e:
        log_error(f"Error in daily runner: {e}")


if __name__ == "__main__":
    main()
