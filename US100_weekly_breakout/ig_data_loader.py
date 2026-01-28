# ig_data_loader.py
import pandas as pd
from trading_ig import IGService
import config

class IGDataLoader:
    def __init__(self, epic=config.SYMBOL,
                 ig_username=config.IG_USERNAME,
                 ig_password=config.IG_PASSWORD,
                 ig_api_key=config.IG_API_KEY):
        self.epic = epic
        self.ig_service = IGService(
            username=ig_username,
            password=ig_password,
            api_key=ig_api_key,
            acc_type="LIVE"
        )
        self.ig_service.create_session()

    def fetch_latest_prices(self, numpoints=50, resolution="1D"):
        """
        Fetch historical prices from IG.
        resolution: "1D" for daily, "1W" for weekly
        Returns DataFrame with columns: open, high, low, close
        """
        raw = self.ig_service.fetch_historical_prices_by_epic(
            epic=self.epic,
            resolution=resolution,
            numpoints=numpoints
        )

        df = pd.DataFrame(raw.get("prices", []))

        if df.empty:
            raise ValueError("No price data returned from IG")

        # Extract mid prices safely
        def safe_mid(row, key):
            try:
                bid = row.get("bid", {})
                ask = row.get("ask", {})
                return (bid.get(key, 0) + ask.get(key, 0)) / 2
            except Exception:
                return 0

        df["open"] = df.apply(lambda row: safe_mid(row, "Open"), axis=1)
        df["high"] = df.apply(lambda row: safe_mid(row, "High"), axis=1)
        df["low"]  = df.apply(lambda row: safe_mid(row, "Low"), axis=1)
        df["close"] = df.apply(lambda row: safe_mid(row, "Close"), axis=1)

        df = df[["open", "high", "low", "close"]].reset_index(drop=True)
        return df

    def fetch_daily_prices(self, numpoints=50):
        """Convenience method for daily prices"""
        return self.fetch_latest_prices(numpoints=numpoints, resolution="1D")

    def fetch_weekly_prices(self, numpoints=50):
        """Convenience method for weekly prices"""
        return self.fetch_latest_prices(numpoints=numpoints, resolution="1W")

    def fetch_account_balance(self):
        """
        Fetch the live balance from IG.
        Returns the first enabled account's balance (float) or None if not found.
        """
        try:
            accounts = self.ig_service.fetch_accounts()
            print("DEBUG: Raw accounts response:", accounts)

            # Handle DataFrame response
            if isinstance(accounts, pd.DataFrame):
                enabled_accounts = accounts[accounts['status'] == 'ENABLED']
                if enabled_accounts.empty:
                    raise ValueError("No enabled accounts found")
                balance = float(enabled_accounts.iloc[0]['balance'])
                return balance

            # Handle dict response (older IG API)
            elif isinstance(accounts, dict):
                accounts_list = accounts.get("accounts")
                if isinstance(accounts_list, dict):
                    accounts_list = [accounts_list]
                enabled_account = next((a for a in accounts_list if a.get("status") == "ENABLED"), None)
                if enabled_account is None:
                    raise ValueError("No enabled accounts found")
                balance = float(enabled_account.get("balance", 0))
                return balance

            else:
                raise TypeError("Unexpected accounts response type")

        except Exception as e:
            print(f"⚠️ Could not fetch account balance: {e}")
            return None
