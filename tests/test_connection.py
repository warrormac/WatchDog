import asyncio
import aiohttp
import ccxt.async_support as ccxt
import ssl
import certifi
import traceback

async def test_raw_binance():
    print("\n--- TEST 1: Raw AIOHTTP to Binance ---")
    url = "https://api.binance.com/api/v3/ping"
    
    # Force the use of the ThreadedResolver to bypass DNS contact issues
    resolver = aiohttp.ThreadedResolver()
    connector = aiohttp.TCPConnector(resolver=resolver, ssl=ssl.create_default_context(cafile=certifi.where()))

    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                print(f"Response: {await response.text()}")
                if response.status == 200:
                    print("✅ TEST 1 PASSED: Native REST is working.")
    except Exception as e:
        print(f"❌ TEST 1 CRASHED: {type(e).__name__} - {e}")

async def test_ccxt_binance():
    print("\n--- TEST 2: CCXT Fetch (Binance) ---")
    client = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'},
        'timeout': 10000,
    })
    client.sslContext = ssl.create_default_context(cafile=certifi.where())
    try:
        # Fetching just 2 candles to test the data pipe
        candles = await client.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=2)
        print(f"✅ TEST 2 PASSED: CCXT Binance returned {len(candles)} candles.")
    except Exception as e:
        print(f"❌ TEST 2 CRASHED: {type(e).__name__} - {e}")
        # Not printing full traceback here unless requested, to keep it clean, 
        # but the error name will tell us exactly what CCXT is complaining about.
    finally:
        await client.close()

async def test_ccxt_kraken():
    print("\n--- TEST 3: CCXT Fetch (Kraken) ---")
    client = ccxt.kraken({'enableRateLimit': True, 'timeout': 10000})
    client.sslContext = ssl.create_default_context(cafile=certifi.where())
    try:
        candles = await client.fetch_ohlcv('BTC/USDT', timeframe='1m', limit=2)
        print(f"✅ TEST 3 PASSED: CCXT Kraken returned {len(candles)} candles.")
    except Exception as e:
        print(f"❌ TEST 3 CRASHED: {type(e).__name__} - {e}")
    finally:
        await client.close()

async def main():
    print("Starting Connection Diagnostics...")
    await test_raw_binance()
    await test_ccxt_binance()
    await test_ccxt_kraken()
    print("\nDiagnostics complete.")

if __name__ == "__main__":
    asyncio.run(main())