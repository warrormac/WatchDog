import pandas as pd
import pandas_ta_classic as ta
from typing import Dict, Any

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates technical indicators and appends them to the DataFrame.
    Expects OHLCV columns: ['open', 'high', 'low', 'close', 'volume'].
    """
    if df.empty or len(df) < 2:
        return df

    # RSI(14)
    df["rsi"] = ta.rsi(df["close"], length=14)
    
    # MACD(12, 26, 9)
    macd_df = ta.macd(df["close"], fast=12, slow=26, signal=9)
    if macd_df is not None:
        df = pd.concat([df, macd_df], axis=1)
    
    # EMA(9, 21, 50, 200)
    df["ema_9"] = ta.ema(df["close"], length=9)
    df["ema_21"] = ta.ema(df["close"], length=21)
    df["ema_50"] = ta.ema(df["close"], length=50)
    df["ema_200"] = ta.ema(df["close"], length=200)
    
    # Bollinger Bands(20, 2)
    bb_df = ta.bbands(df["close"], length=20, std=2)
    if bb_df is not None:
        df = pd.concat([df, bb_df], axis=1)
        
    # ATR(14) for volatility
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
    
    # Volume SMA(20)
    df["vol_sma"] = ta.sma(df["volume"], length=20)
    
    # Stochastic(14, 3)
    stoch_df = ta.stoch(df["high"], df["low"], df["close"], k=14, d=3)
    if stoch_df is not None:
        df = pd.concat([df, stoch_df], axis=1)

    return df
