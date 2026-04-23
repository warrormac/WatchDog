from typing import List, Dict, Any, Literal
from cryptobot.analysis.scorer import FinalScore

class MultiTimeframeConfluence:
    """
    Combines signals from multiple timeframes for a single symbol.
    """
    
    def __init__(self, strategy_config: Dict[str, Any]):
        self.tf_weights = strategy_config.get("timeframe_weights", {
            "1m": 0.1, "5m": 0.2, "15m": 0.3, "1h": 0.25, "4h": 0.15
        })
        self.threshold = strategy_config.get("signal_threshold", 0.55)

    def aggregate(self, scores: List[FinalScore]) -> FinalScore:
        """
        Aggregates multiple FinalScores into a single one.
        Expects all scores to be for the same symbol.
        """
        if not scores:
            return FinalScore("", "", "neutral", 0.0)

        symbol = scores[0].symbol
        long_weighted = 0.0
        short_weighted = 0.0
        all_reasons = []
        all_patterns = []
        
        # Calculate weighted scores
        for score in scores:
            weight = self.tf_weights.get(score.timeframe, 0.2)
            
            # We take the raw confidence of the timeframe if it was directional
            if score.direction == "long":
                long_weighted += score.confidence * weight
            elif score.direction == "short":
                short_weighted += score.confidence * weight
            
            # Collect reasons and patterns for transparency
            if score.confidence > 0:
                tf_prefix = f"[{score.timeframe}] "
                all_reasons.extend([tf_prefix + r for r in score.reasons])
                all_patterns.extend(score.patterns)

        # Determine final direction
        if long_weighted >= short_weighted and long_weighted > 0:
            direction = "long"
            confidence = long_weighted
        elif short_weighted > long_weighted:
            direction = "short"
            confidence = short_weighted
        else:
            direction = "neutral"
            confidence = 0.0
            
        # Ensure we don't return a directional signal if it's below threshold
        final_direction: Literal["long", "short", "neutral"] = "neutral"
        final_confidence = 0.0
        
        if confidence >= self.threshold:
            final_direction = direction
            final_confidence = confidence

        return FinalScore(
            symbol=symbol,
            timeframe="multi",
            direction=final_direction,
            confidence=final_confidence,
            patterns=list(set(all_patterns)),
            reasons=all_reasons,
            timestamp=max(s.timestamp for s in scores)
        )
