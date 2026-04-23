import asyncio
import json
import logging
import websockets
import ccxt.async_support as ccxt
import ssl
import certifi
from typing import Callable, List, Dict, Any
from cryptobot.storage.db import CandleCache

logger = logging.getLogger(__name__)

class ExchangeFeed:
    """
    Maintains a persistent WebSocket connection to public exchange data streams.
    """
    
    BASE_URLS = {
        "binance": "wss://stream.binance.com:9443/stream?streams="
    }

    def __init__(self, exchange_id: str, symbols: List[str], timeframes: List[str], on_tick_callback: Callable[[Dict[str, Any]], Any]):
        self.exchange_id = exchange_id.lower()
        self.symbols_raw = symbols 
        self.symbols_ws = [s.replace("/", "").lower() for s in symbols]
        self.timeframes = timeframes
        self.on_tick_callback = on_tick_callback
        self.is_running = False
        
        # SSL Context
        context = ssl.create_default_context(cafile=certifi.where())

        client_config = {
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'},
        }

        self.client = getattr(ccxt, self.exchange_id)(client_config)
        self.client.sslContext = context

        self.cache = CandleCache(db_path="crypto_pool/cryptobot.db")

    async def fetch_history(self, limit: int = 100):
        logger.info(f"Synchronizing history via CCXT...")
        
        for symbol in self.symbols_raw:
            symbol_key = symbol.replace("/", "")
            for tf in self.timeframes:
                # 1. Load from local cache first
                cached_candles = self.cache.load_candles(symbol_key, tf, limit)
                if cached_candles:
                    for c in cached_candles:
                        await self.on_tick_callback(c)
                    logger.info(f"📁 Local Cache: Loaded {len(cached_candles)} candles for {symbol} {tf}")
                
                # 2. Fetch missing history from API
                latest_ts = self.cache.get_latest_timestamp(symbol_key, tf)
                await self._try_fetch(self.client, [symbol], tf, limit, latest_ts)

    async def _try_fetch(self, client, symbols: List[str], tf: str, limit: int, since_ts: int) -> bool:
        try:
            for symbol in symbols:
                since = since_ts + 1 if since_ts > 0 else None
                
                ohlcv = await client.fetch_ohlcv(symbol, timeframe=tf, limit=limit, since=since)
                
                if not ohlcv:
                    continue

                for candle in ohlcv:
                    normalized = {
                        "exchange": client.id,
                        "symbol": symbol.replace("/", ""),
                        "tf": tf,
                        "ts": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                        "is_closed": True
                    }
                    self.cache.save_candle(normalized)
                    await self.on_tick_callback(normalized)
                
                logger.info(f"✅ [POOLED] {len(ohlcv)} candles for {symbol} {tf}")
                await asyncio.sleep(0.5) # Gentle rate limiting
            return True
        except Exception as e:
            logger.error(f"❌ Sync Failed: {type(e).__name__} - {e}")
            return False

    def _get_stream_url(self) -> str:
        streams = [f"{s}@kline_{tf}" for s in self.symbols_ws for tf in self.timeframes]
        return self.BASE_URLS["binance"] + "/".join(streams)

    async def start(self):
        self.is_running = True
        
        # 1. Warm up using CCXT
        await self.fetch_history()
        
        # 2. Start Live WebSocket
        url = self._get_stream_url()
        while self.is_running:
            try:
                logger.info(f"Connecting to WebSocket...")
                async with websockets.connect(url) as websocket:
                    logger.info(f"Connected to live feed.")
                    async for message in websocket:
                        data = json.loads(message)
                        await self.on_tick_callback(data)
            except Exception as e:
                if not self.is_running: break
                logger.error(f"WebSocket error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def stop(self):
        self.is_running = False
        await self.client.close()
        logger.info("Stopping exchange feed...")