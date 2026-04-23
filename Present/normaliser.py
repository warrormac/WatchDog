from typing import Dict, Any

def normalize_binance_kline(raw_tick: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a Binance kline WebSocket tick.
    Expected format (raw_tick):
    {
        "stream": "btcusdt@kline_1m",
        "data": {
            "e": "kline",     # Event type
            "E": 123456789,   # Event time
            "s": "BTCUSDT",   # Symbol
            "k": {
                "t": 123450000, # Kline start time
                "T": 123459999, # Kline close time
                "s": "BTCUSDT", # Symbol
                "i": "1m",      # Interval
                "f": 100,       # First trade ID
                "L": 200,       # Last trade ID
                "o": "0.0010",  # Open price
                "c": "0.0020",  # Close price
                "h": "0.0025",  # High price
                "l": "0.0015",  # Low price
                "v": "1000",    # Base asset volume
                "n": 100,       # Number of trades
                "x": False,     # Is this kline closed?
                "q": "1.0000",  # Quote asset volume
                "V": "500",     # Taker buy base asset volume
                "Q": "0.500",   # Taker buy quote asset volume
                "B": "123456"   # Ignore
            }
        }
    }
    """
    data = raw_tick.get("data", {})
    k = data.get("k", {})
    
    # Check if this is indeed a kline/tick payload
    if not k:
        return {}

    return {
        "exchange": "binance",
        "symbol":   k.get("s"),
        "tf":       k.get("i"),
        "ts":       k.get("t"),   # millisecond UTC timestamp (start of kline)
        "open":     float(k.get("o", 0)),
        "high":     float(k.get("h", 0)),
        "low":      float(k.get("l", 0)),
        "close":    float(k.get("c", 0)),
        "volume":   float(k.get("v", 0)),
        "is_closed": k.get("x", False) # Important: indicates if this candle just closed
    }
