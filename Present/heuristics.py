import pandas as pd
import numpy as np

class DeepAnalyzer:
    def __init__(self, config):
        self.config = config

    def analyze(self, df, current_price, signal_type):
        warnings = []
        
        # 1. Check Resistance
        resistance = df['high'].tail(20).max()
        if (resistance - current_price) / current_price < 0.003:
            warnings.append("⚠️ HEAVY RESISTANCE NEARBY")

        # 2. Check Volume
        avg_vol = df['volume'].tail(10).mean()
        if df['volume'].iloc[-1] < avg_vol:
            warnings.append("📉 LOW VOLUME (Weak move)")

        # 3. Check RSI
        if df['rsi'].iloc[-1] > 68:
            warnings.append("🎈 RSI OVEREXTENDED (Overbought)")

        if not warnings:
            return "✅ DEEP ANALYSIS: Clean signal."
        
        return " | ".join(warnings)