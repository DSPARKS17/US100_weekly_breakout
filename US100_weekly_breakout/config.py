from dotenv import load_dotenv
import os

load_dotenv()  # load variables from .env

"""
Configuration file for US100 trading strategy.
All constants, paths, and parameters are centralised here.
"""

# ---------------------------
# General Settings
# ---------------------------
SYMBOL = "IX.D.NASDAQ.CASH.IP"
DATA_DIR = "data"
STATE_FILE = "trade_state.json"

# ---------------------------
# EMA Settings
# ---------------------------
EMA_SHORT = 8
EMA_MEDIUM = 50
EMA_LONG = 100
CONSECUTIVE_BARS = 2  # For entry/exit checks

# ---------------------------
# Risk Management
# ---------------------------
ACCOUNT_VALUE = 13500  # Example account size in £
MAX_RISK_PERCENT = 0.02  # Max % of account risked per trade

# ---------------------------
# Strategy Parameters
# ---------------------------
BIG_MOVE_THRESHOLD = 1000  # Points for “big move” after which no new trades
WAIT_FOR_DAILY_EMA = True  # Wait for daily EMA alignment before entry

# ---------------------------
# Notification Settings
# ---------------------------
SEND_EMAILS = False
EMAIL_RECIPIENT = "dannnysparksy17@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "dannnysparksy17@gmail.com"
# EMAIL_APP_PASSWORD = "your_app_password_here"

# ---------------------------
# Visualization Settings
# ---------------------------
PLOT_SIZE = (14, 7)
PLOT_GRID = True

# ---------------------------
# Credentials (from environment variables for security)
# ---------------------------
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
IG_API_KEY  = os.getenv("IG_API_KEY")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM        = os.getenv("TWILIO_FROM")  # Twilio sandbox number
TWILIO_TO          = os.getenv("TWILIO_TO")    # Your WhatsApp number
