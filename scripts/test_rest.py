import asyncio
import ccxt.async_support as ccxt
import logging

logging.basicConfig(level=logging.INFO)

async def test_connectivity():
    # Try global binance
    exchange = ccxt.binance()
    print("Testing connection to binance (global)...")
    try:
        markets = await exchange.load_markets()
        print("✅ Success: Connected to binance global.")
        await exchange.close()
        return
    except Exception as e:
        print(f"❌ Failed: {e}")
        await exchange.close()

    # Try binanceus
    exchange_us = ccxt.binanceus()
    print("\nTesting connection to binanceus...")
    try:
        markets = await exchange_us.load_markets()
        print("✅ Success: Connected to binanceus.")
        await exchange_us.close()
    except Exception as e:
        print(f"❌ Failed: {e}")
        await exchange_us.close()

if __name__ == "__main__":
    asyncio.run(test_connectivity())
