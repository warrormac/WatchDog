import pytest
import pandas as pd
import numpy as np
from cryptobot.analysis.indicators import add_indicators

def test_add_indicators():
    # Create 201 bars of dummy data (enough for EMA 200)
    data = []
    for i in range(210):
        data.append({
            "ts": i,
            "open": 100 + i,
            "high": 110 + i,
            "low": 90 + i,
            "close": 105 + i,
            "volume": 1000
        })
    df = pd.DataFrame(data)
    
    df_with_ind = add_indicators(df)
    
    # Check if indicators columns exist
    assert "rsi" in df_with_ind.columns
    assert "ema_9" in df_with_ind.columns
    assert "ema_200" in df_with_ind.columns
    assert "atr" in df_with_ind.columns
    
    # Check for non-empty results at the end
    assert not np.isnan(df_with_ind["rsi"].iloc[-1])
    assert not np.isnan(df_with_ind["ema_200"].iloc[-1])
    assert not np.isnan(df_with_ind["atr"].iloc[-1])
