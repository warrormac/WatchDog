import pandas as pd
import numpy as np
from typing import Optional, Literal
from dataclasses import dataclass

@dataclass
class PatternSignal:
    name: str
    direction: Literal["long", "short", "neutral"]
    strength: float  # 0.0 to 1.0

def get_candle_metrics(df: pd.DataFrame, index: int = -1):
    """Helper to calculate candle body and shadow sizes."""
    candle = df.iloc[index]
    open_p = candle['open']
    high = candle['high']
    low = candle['low']
    close = candle['close']
    
    body_size = abs(close - open_p)
    candle_range = high - low
    if candle_range == 0:
        return 0, 0, 0, 0, 0
        
    upper_shadow = high - max(open_p, close)
    lower_shadow = min(open_p, close) - low
    
    return body_size, candle_range, upper_shadow, lower_shadow, (close > open_p)

def is_doji(df: pd.DataFrame, threshold: float = 0.1) -> Optional[PatternSignal]:
    """
    Doji: Body is very small relative to the total range.
    """
    if len(df) < 1: return None
    body, candle_range, _, _, _ = get_candle_metrics(df)
    
    if candle_range > 0 and (body / candle_range) < threshold:
        return PatternSignal("doji", "neutral", 0.3)
    return None

def is_hammer(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Hammer (at bottom) / Hanging Man (at top).
    Small body, long lower shadow (at least 2x body), little/no upper shadow.
    """
    if len(df) < 1: return None
    body, candle_range, upper, lower, bullish = get_candle_metrics(df)
    
    if candle_range == 0: return None
    
    # Lower shadow is at least 2x body and upper shadow is very small
    if lower >= (2 * body) and upper <= (0.1 * candle_range) and body > 0:
        # Strength depends on how small the body is relative to the range
        strength = min(1.0, lower / (candle_range * 0.66))
        return PatternSignal("hammer", "long", strength)
    return None

def is_inverted_hammer(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Inverted Hammer / Shooting Star.
    Small body, long upper shadow, little/no lower shadow.
    """
    if len(df) < 1: return None
    body, candle_range, upper, lower, bullish = get_candle_metrics(df)
    
    if candle_range == 0: return None
    
    if upper >= (2 * body) and lower <= (0.1 * candle_range) and body > 0:
        strength = min(1.0, upper / (candle_range * 0.66))
        return PatternSignal("inverted_hammer", "short", strength)
    return None

def is_marubozu(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Marubozu: Full body, virtually no shadows.
    """
    if len(df) < 1: return None
    body, candle_range, upper, lower, bullish = get_candle_metrics(df)
    
    if candle_range > 0 and (body / candle_range) > 0.9:
        direction = "long" if bullish else "short"
        return PatternSignal("marubozu", direction, 0.8)
    return None

def is_spinning_top(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Spinning Top: Small body, long symmetric shadows.
    """
    if len(df) < 1: return None
    body, candle_range, upper, lower, bullish = get_candle_metrics(df)
    
    if candle_range == 0: return None
    
    # Small body (less than 1/3 range) and both shadows are significant
    if (body / candle_range) < 0.33 and upper > body and lower > body:
        return PatternSignal("spinning_top", "neutral", 0.4)
    return None

# --- Two-candle patterns ---

def is_engulfing(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Bullish Engulfing: 2nd candle body completely covers 1st candle body.
    """
    if len(df) < 2: return None
    
    # Prev candle
    p_body, p_range, _, _, p_bullish = get_candle_metrics(df, -2)
    p_open = df.iloc[-2]['open']
    p_close = df.iloc[-2]['close']
    
    # Curr candle
    c_body, c_range, _, _, c_bullish = get_candle_metrics(df, -1)
    c_open = df.iloc[-1]['open']
    c_close = df.iloc[-1]['close']
    
    # Bullish Engulfing
    if not p_bullish and c_bullish:
        if c_close >= p_open and c_open <= p_close:
            return PatternSignal("bullish_engulfing", "long", 0.8)
            
    # Bearish Engulfing
    if p_bullish and not c_bullish:
        if c_close <= p_open and c_open >= p_close:
            return PatternSignal("bearish_engulfing", "short", 0.8)
            
    return None

def is_piercing_line(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Piercing Line (Bullish) / Dark Cloud Cover (Bearish).
    2nd candle closes more than halfway into 1st candle's body.
    """
    if len(df) < 2: return None
    
    # Prev candle
    p_open = df.iloc[-2]['open']
    p_close = df.iloc[-2]['close']
    p_body = abs(p_close - p_open)
    p_bullish = p_close > p_open
    
    # Curr candle
    c_open = df.iloc[-1]['open']
    c_close = df.iloc[-1]['close']
    c_bullish = c_close > c_open
    
    # Piercing Line (Bullish)
    if not p_bullish and c_bullish:
        # Opens below prev close
        if c_open < p_close:
            # Closes above midpoint of prev body
            midpoint = p_close + (p_body / 2)
            if c_close > midpoint and c_close < p_open:
                return PatternSignal("piercing_line", "long", 0.7)
                
    # Dark Cloud Cover (Bearish)
    if p_bullish and not c_bullish:
        # Opens above prev close
        if c_open > p_close:
            # Closes below midpoint of prev body
            midpoint = p_open + (p_body / 2)
            if c_close < midpoint and c_close > p_open:
                return PatternSignal("dark_cloud_cover", "short", 0.7)
                
    return None

def is_tweezers(df: pd.DataFrame, tolerance: float = 0.001) -> Optional[PatternSignal]:
    """
    Tweezer Top (equal highs) / Tweezer Bottom (equal lows).
    """
    if len(df) < 2: return None
    
    p_high = df.iloc[-2]['high']
    p_low = df.iloc[-2]['low']
    c_high = df.iloc[-1]['high']
    c_low = df.iloc[-1]['low']
    
    # Tweezer Bottom
    if abs(p_low - c_low) / (p_low + 1e-9) < tolerance:
        return PatternSignal("tweezer_bottom", "long", 0.6)
        
    # Tweezer Top
    if abs(p_high - c_high) / (p_high + 1e-9) < tolerance:
        return PatternSignal("tweezer_top", "short", 0.6)
        
    return None

# --- Three-candle patterns ---

def is_star(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Morning Star (Bullish) / Evening Star (Bearish).
    1st: Large, 2nd: Small (gap), 3rd: Large (reversal).
    """
    if len(df) < 3: return None
    
    # Candle 1
    m1_body, m1_range, _, _, m1_bullish = get_candle_metrics(df, -3)
    # Candle 2 (Star)
    m2_body, m2_range, _, _, m2_bullish = get_candle_metrics(df, -2)
    # Candle 3
    m3_body, m3_range, _, _, m3_bullish = get_candle_metrics(df, -1)
    
    # Morning Star
    if not m1_bullish and m3_bullish:
        # Star is small body
        if m2_body < (m1_body * 0.3) and m3_body > (m1_body * 0.5):
            # 3rd candle closes deep into 1st candle body
            if df.iloc[-1]['close'] > (df.iloc[-3]['close'] + m1_body * 0.5):
                return PatternSignal("morning_star", "long", 0.9)
                
    # Evening Star
    if m1_bullish and not m3_bullish:
        if m2_body < (m1_body * 0.3) and m3_body > (m1_body * 0.5):
            if df.iloc[-1]['close'] < (df.iloc[-3]['close'] - m1_body * 0.5):
                return PatternSignal("evening_star", "short", 0.9)
                
    return None

def is_soldiers_crows(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Three White Soldiers (Bullish) / Three Black Crows (Bearish).
    Three consecutive large candles of same direction.
    """
    if len(df) < 3: return None
    
    m1_body, _, _, _, m1_bullish = get_candle_metrics(df, -3)
    m2_body, _, _, _, m2_bullish = get_candle_metrics(df, -2)
    m3_body, _, _, _, m3_bullish = get_candle_metrics(df, -1)
    
    # Three White Soldiers
    if m1_bullish and m2_bullish and m3_bullish:
        if m1_body > 0 and m2_body > 0 and m3_body > 0:
            return PatternSignal("three_white_soldiers", "long", 0.8)
            
    # Three Black Crows
    if not m1_bullish and not m2_bullish and not m3_bullish:
        if m1_body > 0 and m2_body > 0 and m3_body > 0:
            return PatternSignal("three_black_crows", "short", 0.8)
            
    return None

def is_inside_bar(df: pd.DataFrame) -> Optional[PatternSignal]:
    """
    Inside Bar: Current candle is completely within previous candle's range.
    Often a consolidation pattern.
    """
    if len(df) < 2: return None
    
    p_high = df.iloc[-2]['high']
    p_low = df.iloc[-2]['low']
    c_high = df.iloc[-1]['high']
    c_low = df.iloc[-1]['low']
    
    if c_high <= p_high and c_low >= p_low:
        return PatternSignal("inside_bar", "neutral", 0.5)
        
    return None
