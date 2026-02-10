# ig_data_loader.py
import os
import pandas as pd
from trading_ig import IGService
import config

CACHE_DIR = "cache"
DAILY_CACHE_FILE = os.path.join(CACHE_DIR, "daily.csv")
WEEKLY_CACHE_FILE = os.path.join(CACHE_DIR, "weekly.csv")

os.makedirs(CACHE_DIR, exist_ok=True)


class IGDataLoader:
    def __init__(
        self,
        epic=config.SYMBOL,
        ig_username=config.IG_USERNAME,
        ig_password=config.IG_PASSWORD,
        ig_api_key=config.IG_API_KEY,
    ):
        self.epic = epic
        self.ig_service = IGService(
            username=ig_username,
            password=ig_password,
            api_key=ig_api_key,
            acc_type="LIVE",
        )
        self.ig_service.create_session()

    # -------------------------------------------------
    # Internal helpers
    # -------------------------------------------------
    def _safe_mid(self, row, key):
        try:
            bid = row.get("bid", {})
            ask = row.get("ask", {})
            return (bid.get(key, 0) + ask.get(key, 0)) / 2
        except Exception:
            return 0

    def _generate_timestamps(self, length, resolution):
        """
        Generate synthetic timestamps when IG does not provide them.
        """
        now = pd.Timestamp.utcnow().normalize()

        if resolution == "1D":
            return pd.date_range(end=now, periods=length, freq="B")

        if resolution == "1W":
            # Generate week-commencing Mondays
            last_monday = now - pd.Timedelta(days=now.weekday())
            return pd.date_range(end=last_monday, periods=length, freq="W-MON")

        raise ValueError(f"Unsupported resolution: {resolution}")

    def _fetch_prices_from_ig(self, numpoints, resolution):
        raw = self.ig_service.fetch_historical_prices_by_epic(
            epic=self.epic,
            resolution=resolution,
            numpoints=numpoints,
        )

        df = pd.DataFrame(raw.get("prices", []))
        if df.empty:
            raise ValueError("No price data returned from IG")

        df["open"] = df.apply(lambda r: self._safe_mid(r, "Open"), axis=1)
        df["high"] = df.apply(lambda r: self._safe_mid(r, "High"), axis=1)
        df["low"] = df.apply(lambda r: self._safe_mid(r, "Low"), axis=1)
        df["close"] = df.apply(lambda r: self._safe_mid(r, "Close"), axis=1)

        timestamps = self._generate_timestamps(len(df), resolution)

        df = (
            df.assign(timestamp=timestamps)
            .set_index("timestamp")
            .sort_index()
        )

        return df[["open", "high", "low", "close"]]

    def _load_cache(self, path):
        if not os.path.exists(path):
            return pd.DataFrame()
        try:
            return pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
        except Exception:
            return pd.DataFrame()

    def _update_cache(self, cache_df, new_df, path):
        if cache_df.empty:
            combined = new_df
        else:
            combined = (
                pd.concat([cache_df, new_df])
                .drop_duplicates()
                .sort_index()
            )

        combined.to_csv(path)
        return combined

    # -------------------------------------------------
    # Public API (unchanged)
    # -------------------------------------------------
    def fetch_daily_prices(self, numpoints=50):
        cache_df = self._load_cache(DAILY_CACHE_FILE)
        ig_df = self._fetch_prices_from_ig(
            numpoints=max(numpoints, 10), resolution="1D"
        )

        missing = ig_df if cache_df.empty else ig_df[~ig_df.index.isin(cache_df.index)]
        full_df = self._update_cache(cache_df, missing, DAILY_CACHE_FILE)

        return full_df.tail(numpoints)

    def fetch_weekly_prices(self, numpoints=50):
        cache_df = self._load_cache(WEEKLY_CACHE_FILE)
        ig_df = self._fetch_prices_from_ig(
            numpoints=max(numpoints, 10), resolution="1W"
        )

        missing = ig_df if cache_df.empty else ig_df[~ig_df.index.isin(cache_df.index)]
        full_df = self._update_cache(cache_df, missing, WEEKLY_CACHE_FILE)

        return full_df.tail(numpoints)

    def fetch_account_balance(self):
        try:
            accounts = self.ig_service.fetch_accounts()

            if isinstance(accounts, pd.DataFrame):
                enabled = accounts[accounts["status"] == "ENABLED"]
                return float(enabled.iloc[0]["balance"])

            if isinstance(accounts, dict):
                accounts_list = accounts.get("accounts", [])
                enabled = next(
                    (a for a in accounts_list if a.get("status") == "ENABLED"), None
                )
                return float(enabled.get("balance", 0)) if enabled else None

        except Exception as e:
            print(f"⚠️ Could not fetch account balance: {e}")
            return None
