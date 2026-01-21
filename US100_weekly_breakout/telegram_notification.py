# telegram_notification.py
import os
import requests
from logger import log_info, log_error

def send_telegram_message(message: str):
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

        if not token or not chat_id:
            raise ValueError("Missing Telegram environment variables")

        url = f"https://api.telegram.org/bot{token}/sendMessage"

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        log_info("Telegram message sent successfully")

    except Exception as e:
        log_error(f"Failed to send Telegram message: {e}")
