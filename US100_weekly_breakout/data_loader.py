import os
import pandas as pd
from utils import add_emas
import config

class DataLoader:
    def __init__(self, symbol=config.SYMBOL, data_dir=config.DATA_DIR):
        self.symbol = symbol
        self.data_dir = data_dir
        self.daily = None
        self.weekly = None
        self.four_hour = None

    def _load_csv(self, timeframe):
        """
        Load CSV for given timeframe: weekly, daily, 4h.
        """
        filepath = os.path.join(self.data_dir, f"{self.symbol}_{timeframe}.csv")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} not found. Please add your OHLCV data.")
        df = pd.read_csv(filepath, index_col='date', parse_dates=True)
        df = add_emas(df, periods=[config.EMA_SHORT, config.EMA_MEDIUM, config.EMA_LONG])
        return df

    def load_all(self):
        """
        Load and prepare all timeframes: weekly, daily, 4h.
        """
        self.weekly = self._load_csv("weekly")
        self.daily = self._load_csv("daily")
        self.four_hour = self._load_csv("4h")
        return self.weekly, self.daily, self.four_hour

    def get_latest_prices(self):
        """
        Return latest close prices for all timeframes.
        """
        latest = {
            "weekly_close": self.weekly['close'].iloc[-1] if self.weekly is not None else None,
            "daily_close": self.daily['close'].iloc[-1] if self.daily is not None else None,
            "4h_close": self.four_hour['close'].iloc[-1] if self.four_hour is not None else None
        }
        return latest

    def refresh(self):
        """
        Reload data from CSVs (useful if new data is added daily).
        """
        return self.load_all()