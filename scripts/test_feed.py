import asyncio
import logging
import sys
import os

# Add the project root to sys.path to allow imports from cryptobot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cryptobot.data.feed import ExchangeFeed
from cryptobot.data.normaliser import normalize_binance_kline

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def main():
    symbols = ["BTC/USDT"]
    timeframes = ["1m"]
    
    async def on_tick(raw_tick):
        normalized = normalize_binance_kline(raw_tick)
        if normalized:
            # Only print if the kline is closed or at regular intervals to avoid flooding the console
            if normalized["is_closed"]:
                print(f"CLOSED CANDLE: {normalized['symbol']} {normalized['tf']} | Close: {normalized['close']}")
            else:
                # Still print something to show it's working
                print(f"LIVE TICK: {normalized['symbol']} {normalized['tf']} | Price: {normalized['close']}")

    feed = ExchangeFeed("binance", symbols, timeframes, on_tick)
    
    print(f"Starting test feed for {symbols} on {timeframes}...")
    try:
        # Run for 30 seconds for testing
        await asyncio.wait_for(feed.start(), timeout=30)
    except asyncio.TimeoutError:
        print("Test completed (timeout reached).")
    finally:
        feed.stop()

if __name__ == "__main__":
    asyncio.run(main())
