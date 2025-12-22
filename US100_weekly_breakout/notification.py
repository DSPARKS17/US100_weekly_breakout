# notification.py
import os
from twilio.rest import Client
from logger import log_info, log_error

def send_whatsapp_message(message: str):
    """
    Send a WhatsApp message via Twilio.
    Cleans environment variables and logs missing ones if any.
    """
    try:
        # Fetch environment variables
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        from_number = os.getenv("TWILIO_FROM", "").strip()
        to_number = os.getenv("TWILIO_TO", "").strip()

        # Check for missing variables
        if not all([account_sid, auth_token, from_number, to_number]):
            raise ValueError(
                f"Missing Twilio env vars: "
                f"SID={'set' if account_sid else 'MISSING'}, "
                f"Token={'set' if auth_token else 'MISSING'}, "
                f"From={'set' if from_number else 'MISSING'}, "
                f"To={'set' if to_number else 'MISSING'}"
            )

        # Initialize Twilio client and send message
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )

        log_info(f"WhatsApp message sent. SID: {msg.sid}")

    except Exception as e:
        log_error(f"Failed to send WhatsApp message: {e}")
