import pytest
import pandas as pd
from cryptobot.analysis.patterns import (
    is_doji, is_hammer, is_inverted_hammer, is_marubozu, is_spinning_top,
    is_engulfing, is_piercing_line, is_tweezers,
    is_star, is_soldiers_crows, is_inside_bar
)

def create_df(open_p, high, low, close):
    return pd.DataFrame([{
        "open": open_p, "high": high, "low": low, "close": close, "volume": 100
    }])

def test_is_doji():
    # Body is 1, range is 100 -> Doji
    df = create_df(100, 150, 50, 101)
    signal = is_doji(df)
    assert signal is not None
    assert signal.name == "doji"
    
    # Body is large -> Not Doji
    df_not = create_df(100, 150, 50, 140)
    assert is_doji(df_not) is None

def test_is_hammer():
    # Small body (2), long lower shadow (8), little upper (0)
    # Open 10, Close 12, Low 2, High 12
    df = create_df(10, 12, 2, 12)
    signal = is_hammer(df)
    assert signal is not None
    assert signal.name == "hammer"
    assert signal.direction == "long"

def test_is_inverted_hammer():
    # Small body (2), long upper shadow (8), little lower (0)
    df = create_df(10, 20, 10, 12)
    signal = is_inverted_hammer(df)
    assert signal is not None
    assert signal.name == "inverted_hammer"
    assert signal.direction == "short"

def test_is_marubozu():
    # Full body, no shadows
    df = create_df(100, 150, 100, 150)
    signal = is_marubozu(df)
    assert signal is not None
    assert signal.name == "marubozu"
    assert signal.direction == "long"

def test_is_spinning_top():
    # Small body (10), long shadows (20 each)
    # Range 50: Low 70, Open 90, Close 100, High 120
    df = create_df(90, 120, 70, 100)
    signal = is_spinning_top(df)
    assert signal is not None
    assert signal.name == "spinning_top"

def test_is_engulfing():
    # Bullish Engulfing
    df = pd.DataFrame([
        {"open": 100, "high": 105, "low": 95, "close": 98, "volume": 100}, # Bearish
        {"open": 97, "high": 110, "low": 90, "close": 105, "volume": 100}  # Bullish, covers prev body
    ])
    signal = is_engulfing(df)
    assert signal is not None
    assert signal.name == "bullish_engulfing"

def test_is_piercing_line():
    # Piercing Line
    df = pd.DataFrame([
        {"open": 100, "high": 105, "low": 80, "close": 80, "volume": 100}, # Large bearish
        {"open": 75, "high": 95, "low": 70, "close": 92, "volume": 100}   # Bullish, closes > 50% into prev body
    ])
    signal = is_piercing_line(df)
    assert signal is not None
    assert signal.name == "piercing_line"

def test_is_tweezers():
    # Tweezer Bottom
    df = pd.DataFrame([
        {"open": 100, "high": 105, "low": 90, "close": 92, "volume": 100},
        {"open": 92, "high": 100, "low": 90, "close": 98, "volume": 100}
    ])
    signal = is_tweezers(df)
    assert signal is not None
    assert signal.name == "tweezer_bottom"

def test_is_star():
    # Morning Star
    df = pd.DataFrame([
        {"open": 100, "high": 105, "low": 80, "close": 80, "volume": 100}, # Large Bearish
        {"open": 78, "high": 82, "low": 75, "close": 80, "volume": 100},  # Star
        {"open": 82, "high": 95, "low": 80, "close": 94, "volume": 100}   # Bullish reversal
    ])
    signal = is_star(df)
    assert signal is not None
    assert signal.name == "morning_star"

def test_is_soldiers_crows():
    # Three White Soldiers
    df = pd.DataFrame([
        {"open": 100, "high": 110, "low": 100, "close": 110, "volume": 100},
        {"open": 110, "high": 120, "low": 110, "close": 120, "volume": 100},
        {"open": 120, "high": 130, "low": 120, "close": 130, "volume": 100}
    ])
    signal = is_soldiers_crows(df)
    assert signal is not None
    assert signal.name == "three_white_soldiers"

def test_is_inside_bar():
    # Inside Bar
    df = pd.DataFrame([
        {"open": 100, "high": 120, "low": 80, "close": 110, "volume": 100},
        {"open": 90, "high": 110, "low": 85, "close": 95, "volume": 100}
    ])
    signal = is_inside_bar(df)
    assert signal is not None
    assert signal.name == "inside_bar"
