import pandas as pd
from trading_ig import IGService
import config

class IGDataLoader:
    def __init__(self, epic=config.SYMBOL, ig_username=config.IG_USERNAME,
                 ig_password=config.IG_PASSWORD, ig_api_key=config.IG_API_KEY):
        self.epic = epic
        self.ig_service = IGService(
            username=ig_username,
            password=ig_password,
            api_key=ig_api_key,
            acc_type="LIVE"
        )
        self.ig_service.create_session()

    def fetch_latest_prices(self, numpoints=5):
        # Fetch raw prices
        raw = self.ig_service.fetch_historical_prices_by_epic(
            epic=self.epic,
            resolution="1D",
            numpoints=numpoints
        )

        # Convert to DataFrame
        df = pd.DataFrame(raw["prices"])

        # Extract mid prices safely
        def safe_mid(row, key):
            try:
                return (row["bid"].get(key) + row["ask"].get(key)) / 2
            except AttributeError:
                return 0

        df["open"] = df.apply(lambda row: safe_mid(row, "Open"), axis=1)
        df["high"] = df.apply(lambda row: safe_mid(row, "High"), axis=1)
        df["low"]  = df.apply(lambda row: safe_mid(row, "Low"), axis=1)
        df["close"] = df.apply(lambda row: safe_mid(row, "Close"), axis=1)

        # Keep only necessary columns
        df = df[["open", "high", "low", "close"]]

        return df






