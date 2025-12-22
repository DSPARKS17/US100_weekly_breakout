import os
import pandas as pd
import config
from ig_data_loader import IGDataLoader
from utils import add_emas 

class DataLoader:
    def __init__(self, symbol=config.SYMBOL, data_dir=config.DATA_DIR, live=False):
        self.symbol = symbol
        self.data_dir = data_dir
        self.live = live
        self.daily = None
        self.weekly = None
        self.four_hour = None
        if self.live:
            self.ig_loader = IGDataLoader(epic=self.symbol)

    def _load_csv(self, timeframe):
        filepath = os.path.join(self.data_dir, f"{self.symbol}_{timeframe}.csv")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} not found. Please add your OHLCV data.")
        df = pd.read_csv(filepath, index_col='date', parse_dates=True)
        df = add_emas(df, periods=[config.EMA_SHORT, config.EMA_MEDIUM, config.EMA_LONG])
        return df

    def load_all(self):
        if self.live:
            df = self.ig_loader.fetch_latest_prices()  # must return OHLCV DataFrame
            # TODO: split df into daily, weekly, 4h
            self.daily = df
            self.weekly = df  # placeholder
            self.four_hour = df  # placeholder
        else:
            self.weekly = self._load_csv("weekly")
            self.daily = self._load_csv("daily")
            self.four_hour = self._load_csv("4h")
        return self.weekly, self.daily, self.four_hour