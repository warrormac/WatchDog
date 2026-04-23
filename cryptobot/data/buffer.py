import pandas as pd
from typing import Dict, List, Any, Optional
from collections import deque

class RingBuffer:
    """
    Maintains a fixed-size buffer of closed OHLCV candles for a specific symbol/timeframe.
    Converts data to pandas DataFrames for analysis.
    """
    
    def __init__(self, capacity: int = 500):
        self.capacity = capacity
        # Use a deque for efficient O(1) append/pop at the limits
        self._data = deque(maxlen=capacity)
        # Track the last timestamp to avoid duplicate candles
        self._last_ts = -1

    def add(self, candle: Dict[str, Any]) -> bool:
        """
        Adds a normalized candle to the buffer if it's closed and new.
        Returns True if added, False otherwise.
        """
        if not candle.get("is_closed"):
            return False
            
        ts = candle.get("ts")
        if ts is None or ts <= self._last_ts:
            return False
            
        # We only store the relevant numeric fields
        self._data.append({
            "ts": candle["ts"],
            "open": candle["open"],
            "high": candle["high"],
            "low": candle["low"],
            "close": candle["close"],
            "volume": candle["volume"]
        })
        self._last_ts = ts
        return True

    def get_df(self) -> pd.DataFrame:
        """
        Returns the current buffer as a pandas DataFrame.
        """
        if not self._data:
            return pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])
            
        df = pd.DataFrame(list(self._data))
        # Ensure correct types
        df["ts"] = pd.to_numeric(df["ts"])
        df["open"] = pd.to_numeric(df["open"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["close"] = pd.to_numeric(df["close"])
        df["volume"] = pd.to_numeric(df["volume"])
        return df

    def __len__(self):
        return len(self._data)

class BufferManager:
    """
    Manages multiple RingBuffers for different symbol/timeframe pairs.
    """
    
    def __init__(self, capacity: int = 500):
        self.capacity = capacity
        # Key: "SYMBOL_TIMEFRAME"
        self.buffers: Dict[str, RingBuffer] = {}

    def update(self, normalized_tick: Dict[str, Any]) -> bool:
        """
        Routes a normalized tick to the correct buffer.
        """
        symbol = normalized_tick.get("symbol")
        tf = normalized_tick.get("tf")
        
        if not symbol or not tf:
            return False
            
        key = f"{symbol}_{tf}"
        if key not in self.buffers:
            self.buffers[key] = RingBuffer(capacity=self.capacity)
            
        return self.buffers[key].add(normalized_tick)

    def get_buffer(self, symbol: str, tf: str) -> Optional[RingBuffer]:
        return self.buffers.get(f"{symbol}_{tf}")
