import asyncio
import json
import websockets
import yaml
import logging
import os
import sys
from heuristics import DeepAnalyzer

# Project pathing - so we can still find the Vault folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# SELF-CONTAINED IMPORTS
from Vault.db import Database, RingBuffer
from normaliser import normalize_binance_kline
from scorer import SignalScorer
from indicators import add_indicators

logging.basicConfig(level=logging.INFO, format="%(asctime)s - ORACLE - %(message)s")
logger = logging.getLogger("oracle")

class OracleService:
    def __init__(self):
        with open("config/master.yaml", "r") as f:
            self.config = yaml.safe_load(f)
            
        self.db = Database(db_path=self.config["vault"]["database_path"])
        self.scorer = SignalScorer(self.config["present"]) 
        self.buffers = {} 
        self.symbols = self.config["trading"]["symbols"]
        self.timeframes = self.config["trading"]["timeframes"]
        self.is_running = True

    async def warm_up(self):
        """Loads historical candles from Vault into memory buffers."""
        limit = self.config["past"].get("warmup_candles", 250)
        logger.info(f"Warming up memory buffers with {limit} candles...")
        
        for sym in self.symbols:
            for tf in self.timeframes:
                key = f"{sym}_{tf}"
                self.buffers[key] = RingBuffer(capacity=limit + 50)
                history = self.db.load_candles(sym, tf, limit=limit)
                for candle in history:
                    self.buffers[key].add(candle)
        logger.info("Buffers warmed. Ready for live data.")

    async def process_candle(self, candle):
        """Analyze a closed candle and save signals individually to Vault."""
        sym, tf = candle["symbol"], candle["tf"]
        key = f"{sym}_{tf}"
        
        if key in self.buffers:
            self.buffers[key].add(candle)
            
            # Get DataFrame and add technical indicators
            df = self.buffers[key].get_df()
            df_with_ind = add_indicators(df)
            
            # Use your custom Scorer logic
            score = self.scorer.score_df(df_with_ind, sym, tf)
            
            if score.confidence >= self.config["present"]["signal_threshold"]:
            
                analyzer = DeepAnalyzer(self.config)
                
                # Generate the warning report
                warning_report = analyzer.analyze(df_with_ind, candle["close"], score.direction)
                
                # Save to DB (Make sure your Database.save_signal accepts the new 'warning' argument)
                self.db.save_signal(
                    sym, 
                    score.direction, 
                    candle["close"], 
                    score.confidence,
                    warning_report  # <--- Pass the new column data
                )
                logger.info(f"🚨 SIGNAL DETECTED: {sym} with analysis: {warning_report}")
            
    async def run_ws(self):
        """Main WebSocket loop with reconnect logic."""
        ws_url = self.config["present"]["exchange_ws"]
        streams = [f"{s.lower()}@kline_{tf}" for s in self.symbols for tf in self.timeframes]
        full_url = f"{ws_url}?streams={'/'.join(streams)}"
        
        while self.is_running:
            try:
                logger.info("Connecting to Binance WebSocket...")
                async with websockets.connect(full_url) as ws:
                    logger.info("WebSocket Connected.")
                    async for message in ws:
                        if not self.is_running: break
                        data = json.loads(message)
                        normalized = normalize_binance_kline(data)
                        
                        # Only process when a 1-minute candle actually closes
                        if normalized and normalized.get("is_closed"):
                            self.db.save_candle(normalized)
                            await self.process_candle(normalized)
            except Exception as e:
                if self.is_running:
                    logger.error(f"WS Error: {e}. Reconnecting in 5s...")
                    await asyncio.sleep(5)

    async def stop(self):
        """Graceful shutdown sequence."""
        logger.info("Shutting down Oracle...")
        self.is_running = False

async def main():
    oracle = OracleService()
    try:
        await oracle.warm_up()
        await oracle.run_ws()
    except asyncio.CancelledError:
        await oracle.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass