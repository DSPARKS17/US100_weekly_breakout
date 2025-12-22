import os
from twilio.rest import Client
from logger import log_info, log_error

def send_whatsapp_message(message: str):
    """
    Send a WhatsApp message via Twilio.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM")
        to_number = os.getenv("TWILIO_TO")

        if not all([account_sid, auth_token, from_number, to_number]):
            raise ValueError("Missing Twilio environment variables")

        client = Client(account_sid, auth_token)

        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )

        log_info(f"WhatsApp message sent. SID: {msg.sid}")

    except Exception as e:
        log_error(f"Failed to send WhatsApp message: {e}")

