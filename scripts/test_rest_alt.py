import asyncio
import ccxt.async_support as ccxt

async def test_extra_endpoints():
    endpoints = [
        "https://api1.binance.com",
        "https://api2.binance.com",
        "https://api3.binance.com"
    ]
    
    for url in endpoints:
        print(f"Testing {url}...")
        exchange = ccxt.binance({
            'urls': {
                'api': {
                    'public': url + '/api/v3',
                }
            }
        })
        try:
            await exchange.load_markets()
            print(f"✅ Success: {url} is reachable.")
            await exchange.close()
            return True
        except Exception as e:
            print(f"❌ Failed: {e}")
            await exchange.close()
    return False

if __name__ == "__main__":
    asyncio.run(test_extra_endpoints())
