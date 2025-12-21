"""
Configuration file for US100 trading strategy.
All constants, paths, and parameters are centralized here.
"""

# ---------------------------
# General Settings
# ---------------------------
SYMBOL = "US100"
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
ACCOUNT_VALUE = 10000  # Example account size in £
MAX_RISK_PERCENT = 0.02  # Max % of account risked per trade

# ---------------------------
# Strategy Parameters
# ---------------------------
BIG_MOVE_THRESHOLD = 1000  # Points for “big move” after which no new trades
WAIT_FOR_DAILY_EMA = True  # Wait for daily EMA alignment before entry

# ---------------------------
# Notification Settings
# ---------------------------
SEND_EMAILS = True
EMAIL_RECIPIENT = "dannnysparksy17@gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "dannnysparksy17@gmail.com"
EMAIL_APP_PASSWORD = "kumuaddqqdpgspho"

# ---------------------------
# Visualization Settings
# ---------------------------
PLOT_SIZE = (14, 7)
PLOT_GRID = True