import pandas as pd

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def compute_volatility(df, window=4):
    ranges = df['high'] - df['low']
    return ranges.rolling(window=window).mean()

def compute_multiple_emas(df, periods=[8, 50, 100]):
    for p in periods:
        df[f'EMA{p}'] = df['close'].ewm(span=p, adjust=False).mean()
    return df

def compute_stop_loss(df, period=100, vol_multiplier=1):
    df['stop_loss'] = df['EMA100'] - vol_multiplier * compute_volatility(df)
    return df