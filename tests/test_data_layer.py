import pytest
import pandas as pd
from cryptobot.data.normaliser import normalize_binance_kline
from cryptobot.data.buffer import RingBuffer, BufferManager

def test_normalize_binance_kline():
    raw_tick = {
        "data": {
            "e": "kline",
            "s": "BTCUSDT",
            "k": {
                "t": 1712000000000,
                "s": "BTCUSDT",
                "o": "70000.0",
                "h": "70100.0",
                "l": "69900.0",
                "c": "70050.0",
                "v": "10.5",
                "i": "1m",
                "x": True
            }
        }
    }
    
    normalized = normalize_binance_kline(raw_tick)
    
    assert normalized["symbol"] == "BTCUSDT"
    assert normalized["open"] == 70000.0
    assert normalized["is_closed"] is True
    assert normalized["tf"] == "1m"

def test_ring_buffer_add_only_closed():
    buffer = RingBuffer(capacity=5)
    
    # Non-closed candle should not be added
    candle_open = {"ts": 1, "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1, "is_closed": False}
    assert buffer.add(candle_open) is False
    assert len(buffer) == 0
    
    # Closed candle should be added
    candle_closed = {"ts": 1, "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1, "is_closed": True}
    assert buffer.add(candle_closed) is True
    assert len(buffer) == 1

def test_ring_buffer_duplicates():
    buffer = RingBuffer(capacity=5)
    candle = {"ts": 100, "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 1, "is_closed": True}
    
    buffer.add(candle)
    # Adding same timestamp should fail
    assert buffer.add(candle) is False
    assert len(buffer) == 1

def test_buffer_manager_routing():
    manager = BufferManager(capacity=10)
    tick_btc = {"symbol": "BTCUSDT", "tf": "1m", "ts": 1, "open": 1, "high": 2, "low": 0, "close": 1.5, "volume": 1, "is_closed": True}
    tick_eth = {"symbol": "ETHUSDT", "tf": "1m", "ts": 1, "open": 1, "high": 2, "low": 0, "close": 1.5, "volume": 1, "is_closed": True}
    
    manager.update(tick_btc)
    manager.update(tick_eth)
    
    assert len(manager.get_buffer("BTCUSDT", "1m")) == 1
    assert len(manager.get_buffer("ETHUSDT", "1m")) == 1
    
    df = manager.get_buffer("BTCUSDT", "1m").get_df()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.iloc[0]["ts"] == 1
