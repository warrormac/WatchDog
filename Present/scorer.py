from dataclasses import dataclass, field
import logging
from typing import List, Literal, Dict, Any, Optional
import pandas as pd
from patterns import (
    PatternSignal, is_doji, is_hammer, is_inverted_hammer, is_marubozu,
    is_spinning_top, is_engulfing, is_piercing_line, is_tweezers,
    is_star, is_soldiers_crows, is_inside_bar
)

logger = logging.getLogger(__name__)

@dataclass
class FinalScore:
    symbol: str
    timeframe: str
    direction: Literal["long", "short", "neutral"]
    confidence: float
    patterns: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    timestamp: int = 0

class SignalScorer:
    def __init__(self, strategy_config: Dict[str, Any]):
        self.threshold = strategy_config.get("signal_threshold", 0.55)
        self.pattern_weights = strategy_config.get("pattern_weights", {})
        self.indicator_weights = strategy_config.get("indicator_weights", {})

    def score_df(self, df: pd.DataFrame, symbol: str, timeframe: str) -> FinalScore:
        """
        Analyzes a DataFrame and returns a FinalScore.
        """
        if df.empty:
            return FinalScore(symbol, timeframe, "neutral", 0.0)

        rsi_val = df.iloc[-1].get("rsi", 0)
        ema9 = df.iloc[-1].get("ema_9", 0)
        # logger.info(f"Checking {symbol} {timeframe} - RSI: {rsi_val}, EMA9: {ema9}, Rows: {len(df)}")
        
        long_score = 0.0
        short_score = 0.0
        patterns_found = []
        reasons = []
        
        # 1. Check Patterns
        pattern_funcs = [
            is_doji, is_hammer, is_inverted_hammer, is_marubozu,
            is_spinning_top, is_engulfing, is_piercing_line, is_tweezers,
            is_star, is_soldiers_crows, is_inside_bar
        ]
        
        for func in pattern_funcs:
            signal = func(df)
            if signal:
                weight = self.pattern_weights.get(signal.name, 0.5)
                score_contribution = signal.strength * weight
                
                patterns_found.append(signal.name)
                reasons.append(f"Pattern: {signal.name} ({signal.direction})")
                
                if signal.direction == "long":
                    long_score += score_contribution
                elif signal.direction == "short":
                    short_score += score_contribution
                # Neutral patterns like doji/spinning_top/inside_bar don't add to directional score
                # but could be used for confirmation in more complex logic

        # 2. Check Indicators (using the last row)
        last = df.iloc[-1]
        
        # RSI
        if "rsi" in df.columns:
            rsi = last["rsi"]
            if rsi is not None and not pd.isna(rsi):
                if rsi < 30:
                    long_score += self.indicator_weights.get("rsi_oversold", 0.7)
                    reasons.append(f"RSI Oversold: {rsi:.1f}")
                elif rsi > 70:
                    short_score += self.indicator_weights.get("rsi_overbought", 0.7)
                    reasons.append(f"RSI Overbought: {rsi:.1f}")

        # EMA Crossovers
        if "ema_9" in df.columns and "ema_21" in df.columns:
            ema9_curr = last["ema_9"]
            ema21_curr = last["ema_21"]
            ema9_prev = df.iloc[-2]["ema_9"]
            ema21_prev = df.iloc[-2]["ema_21"]
            
            # Ensure all values are available
            if all(v is not None and not pd.isna(v) for v in [ema9_curr, ema21_curr, ema9_prev, ema21_prev]):
                if ema9_curr > ema21_curr and ema9_prev <= ema21_prev:
                    long_score += self.indicator_weights.get("ema_golden_cross", 0.8)
                    reasons.append("EMA Golden Cross (9/21)")
                elif ema9_curr < ema21_curr and ema9_prev >= ema21_prev:
                    short_score += self.indicator_weights.get("ema_death_cross", 0.8)
                    reasons.append("EMA Death Cross (9/21)")

        # Determine final direction
        if long_score >= short_score and long_score > 0:
            direction = "long"
            confidence = min(1.0, long_score / 2.0) # Normalizing score
        elif short_score > long_score:
            direction = "short"
            confidence = min(1.0, short_score / 2.0)
        else:
            direction = "neutral"
            confidence = 0.0
            
        return FinalScore(
            symbol=symbol,
            timeframe=timeframe,
            direction=direction if confidence >= self.threshold else "neutral",
            confidence=confidence if confidence >= self.threshold else 0.0,
            patterns=patterns_found,
            reasons=reasons,
            timestamp=int(last["ts"])
        )
