from datetime import datetime
import os
import pandas as pd
import config
from ig_data_loader import IGDataLoader
from notification import send_whatsapp_message
from telegram_notification import send_telegram_message
from logger import log_info, log_error
from trade_logic import should_open_trade, should_close_trade, get_stop_loss, position_size, can_reenter
from trade_state import load_state, save_state

# Fallback account value if IG balance cannot be fetched
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
        daily_df = loader.fetch_daily_prices(numpoints=50)
        weekly_df = loader.fetch_weekly_prices(numpoints=50)
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
        # Latest daily values
        # ---------------------------
        last_daily = daily_df.iloc[-2]
        open_price = float(last_daily['open'])
        high_price = float(last_daily['high'])
        low_price = float(last_daily['low'])
        close_price = float(last_daily['close'])
        ema50 = float(last_daily['EMA50'])
        ema100 = float(last_daily['EMA100'])
        ema8 = float(last_daily['EMA8'])

        # ---------------------------
        # Latest weekly values
        # ---------------------------
        last_weekly = weekly_df.iloc[-1]
        prev_weekly = weekly_df.iloc[-2]
        weekly_close_last = float(last_weekly['close'])
        weekly_close_prev = float(prev_weekly['close'])
        weekly_ema50 = float(last_weekly['EMA50'])
        weekly_ema8_last = float(last_weekly['EMA8'])
        weekly_ema8_prev = float(prev_weekly['EMA8'])

        weekly_trend_valid = weekly_close_last > weekly_ema50
        weekly_window_valid = (weekly_close_prev > weekly_ema8_prev) and (weekly_close_last > weekly_ema8_last)

        # ---------------------------
        # Load trade state
        # ---------------------------
        state = load_state()
        in_trade = state.get("position") is not None

        # ---------------------------
        # Suggested position size
        # ---------------------------
        suggested_size = position_size(account_value, close_price)

        # ---------------------------
        # Compose message
        # ---------------------------
        if in_trade:
            entry_price = state['position']['entry_price']
            pnl = (close_price - entry_price) * state['position']['size']
            big_move_done = state.get("big_move_done", False)
            action_msg = (
                f"Trade Status:\n🟢 IN TRADE\n"
                f"Entry price: {entry_price:.2f}\n"
                f"Current move: {close_price - entry_price:+.0f} points\n"
                f"Big move reached: {'YES' if big_move_done else 'NO'}\n"
                f"Position size: £{state['position']['size']:.2f} / point\n\n"
                f"📌 Action:\n➡️ Hold position"
            )
        else:
            entry_allowed = should_open_trade(weekly_df, daily_df) and not state.get("big_move_done", False)
            reentry_allowed = can_reenter(weekly_df, daily_df, big_move_done=state.get("big_move_done", False))
            action_msg = (
                f"Trade Status:\n🟢 NOT IN TRADE\n\n"
                f"Entry Conditions:\n"
                f"Weekly trend: {'VALID' if weekly_trend_valid else 'INVALID'}\n"
                f"Daily trend: {'VALID' if (close_price > ema50 and close_price > ema100) else 'INVALID'}\n"
                f"Re-entry allowed: {'YES' if reentry_allowed else 'NO'}\n"
                f"Big move lockout: {'YES' if state.get('big_move_done', False) else 'NO'}\n\n"
                f"If opened today:\nSuggested size: £{suggested_size:.2f} / point\n"
                f"Stop loss: {get_stop_loss(daily_df):.2f} (Daily EMA100)\n\n"
                f"📌 Action:\n➡️ {'Consider OPENING a long position' if entry_allowed else 'Do nothing'}"
            )

        # ---------------------------
        # Format weekly last 2 close dates
        # ---------------------------
        try:
            weekly_dates = weekly_df.index[-2:].to_list()
            weekly_dates_str = [d.strftime('%Y-%m-%d') if isinstance(d, pd.Timestamp) else str(d) for d in weekly_dates]
        except Exception:
            weekly_dates_str = ['N/A', 'N/A']

        # ---------------------------
        # Full message
        # ---------------------------
        msg_lines = [
            f"📊 {config.SYMBOL} Daily Strategy Update",
            f"Date: {datetime.now().strftime('%Y-%m-%d')}\n",
            f"Account Value: £{account_value:.2f}\n",
            "Daily:",
            f"Close: {close_price:.2f}",
            f"EMA 50: {ema50:.2f} ({'Above ✅' if close_price > ema50 else 'Below ❌'})",
            f"EMA 100: {ema100:.2f} ({'Above ✅' if close_price > ema100 else 'Below ❌'})",
            f"EMA 8: {ema8:.2f}\n",
            "Weekly:",
            f"Close above EMA50: {weekly_close_last:.2f} vs EMA50: {weekly_ema50:.2f} ({'✅' if weekly_trend_valid else '❌'})",
            f"2 consecutive closes above EMA8 ({weekly_dates_str[0]} / {weekly_dates_str[1]}): "
            f"{weekly_close_prev:.2f} / {weekly_close_last:.2f} vs EMA8: {weekly_ema8_prev:.2f} / {weekly_ema8_last:.2f} "
            f"({'✅' if weekly_window_valid else '❌'})\n",
            action_msg
        ]

        message = "\n".join(msg_lines)

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

