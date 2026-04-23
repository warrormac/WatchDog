import asyncio
import aiohttp # type: ignore
import yaml  # type: ignore
import logging
import os
import sys

# Allow the script to find the Vault and config folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Vault.db import Database

# Set up independent logging for this specific service
logging.basicConfig(level=logging.INFO, format="%(asctime)s - HISTORIAN - %(message)s")
logger = logging.getLogger("historian")

class HistorianService:
    def __init__(self):
        # 1. Load the Master Config
        with open("config/master.yaml", "r") as f:
            self.config = yaml.safe_load(f)
            
        # 2. Connect to the Vault
        self.db = Database(db_path=self.config["vault"]["database_path"])
        
        # 3. Apply settings
        self.symbols = self.config["trading"]["symbols"]
        self.timeframes = self.config["trading"]["timeframes"]
        self.api_url = self.config["past"]["exchange_api"]
        self.limit = self.config["past"]["warmup_candles" ]
        self.interval = self.config["past"]["sync_interval_hours"] * 3600 # Convert hours to seconds

    async def sync_data(self):
        """Pulls missing historical data from Binance and commits it to the Vault."""
        logger.info(f"Initiating historical sync for {len(self.symbols)} assets...")
        
        async with aiohttp.ClientSession() as session:
            for symbol in self.symbols:
                for tf in self.timeframes:
                    
                    # Check the Vault to see the last timestamp we downloaded
                    latest_ts = self.db.get_latest_timestamp(symbol, tf)
                    
                    # Build the URL
                    url = f"{self.api_url}?symbol={symbol}&interval={tf}&limit={self.limit}"
                    if latest_ts > 0:
                        # Only ask Binance for candles newer than what we already have
                        url += f"&startTime={latest_ts + 1}"
                        
                    try:
                        async with session.get(url) as response:
                            if response.status != 200:
                                logger.error(f"❌ API rejected request for {symbol} {tf}")
                                continue
                                
                            data = await response.json()
                            if not data:
                                logger.info(f"✅ {symbol} {tf} is fully up to date.")
                                continue
                                
                            # Save new data to Vault
                            for candle in data:
                                normalized = {
                                    "exchange": "binance",
                                    "symbol": symbol,
                                    "tf": tf,
                                    "ts": candle[0],
                                    "open": float(candle[1]),
                                    "high": float(candle[2]),
                                    "low": float(candle[3]),
                                    "close": float(candle[4]),
                                    "volume": float(candle[5]),
                                    "is_closed": True
                                }
                                self.db.save_candle(normalized)
                                
                            logger.info(f"📥 Saved {len(data)} new candles for {symbol} {tf}")
                            await asyncio.sleep(0.5) # Gentle rate-limiting pause
                            
                    except Exception as e:
                        logger.error(f"❌ Connection error on {symbol} {tf}: {e}")

    async def run_forever(self):
        """The main service loop."""
        logger.info("Service Started. Press Ctrl+C to stop.")
        while True:
            await self.sync_data()
            logger.info(f"Sync complete. Historian is sleeping for {self.config['past']['sync_interval_hours']} hour(s).")
            await asyncio.sleep(self.interval)

if __name__ == "__main__":
    service = HistorianService()
    try:
        asyncio.run(service.run_forever())
    except KeyboardInterrupt:
        logger.info("Historian gracefully shutting down.")