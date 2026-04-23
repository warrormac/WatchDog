import asyncio
import logging
from typing import Dict, Any, List, Optional
from cryptobot.data.buffer import BufferManager
from cryptobot.analysis.indicators import add_indicators
from cryptobot.analysis.scorer import SignalScorer, FinalScore
from cryptobot.analysis.multi_tf import MultiTimeframeConfluence

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Core engine that consumes closed candles, runs analysis, 
    and emits trading signals.
    """
    
    def __init__(self, settings: Dict[str, Any], strategy: Dict[str, Any]):
        self.symbols = settings.get("symbols", [])
        self.timeframes = settings.get("timeframes", [])
        
        self.buffer_manager = BufferManager(capacity=500)
        self.scorer = SignalScorer(strategy)
        self.mtf_confluence = MultiTimeframeConfluence(strategy)
        
        self.input_queue = asyncio.Queue()
        self.output_queue = asyncio.Queue()
        self.is_running = False

    async def process_candle(self, normalized_candle: Dict[str, Any]):
        """
        Receives a closed candle, updates buffer, and checks for signals.
        """
        symbol = normalized_candle["symbol"]
        tf = normalized_candle["tf"]
        
        # 1. Update buffer with closed candle
        if not self.buffer_manager.update(normalized_candle):
            return

        # Add this to verify warm-up
        buf = self.buffer_manager.get_buffer(symbol, tf)
        if len(buf) % 50 == 0:
            logger.info(f"📈 Warming up {symbol} {tf}: {len(buf)}/500 candles loaded.")
            
        logger.debug(f"Closed candle received for {symbol} {tf}. Running analysis...")

        # 2. Run analysis for this symbol/timeframe
        # Note: In a real system we might want to wait for multiple TFs to close 
        # or just check the latest available state for all TFs.
        
        all_tf_scores = []
        for check_tf in self.timeframes:
            buf = self.buffer_manager.get_buffer(symbol, check_tf)
            if buf and len(buf) >= 2: # Min 2 bars to check for crossovers/patterns
                df = buf.get_df()
                # Indicators might still be NaN if len(df) < indicator_length, 
                # but the scorer now handles this gracefully.
                df = add_indicators(df)
                score = self.scorer.score_df(df, symbol, check_tf)
                all_tf_scores.append(score)

        if not all_tf_scores:
            return

        # 3. Combine multi-timeframe results
        final_signal = self.mtf_confluence.aggregate(all_tf_scores)
        
        # 4. If we have a directional signal above threshold, emit it
        if final_signal.direction != "neutral":
            logger.info(f"SIGNAL GENERATED: {final_signal.direction.upper()} {symbol} (Conf: {final_signal.confidence:.2f})")
            await self.output_queue.put(final_signal)

    async def start(self):
        """Main loop consuming from the input queue."""
        self.is_running = True
        logger.info("Decision Engine started.")
        
        while self.is_running:
            try:
                # Get a normalized candle from the feed
                candle = await self.input_queue.get()
                if candle:
                    await self.process_candle(candle)
                self.input_queue.task_done()
            except Exception as e:
                logger.error(f"Error in Decision Engine: {e}", exc_info=True)
                await asyncio.sleep(1)

    def stop(self):
        self.is_running = False
        logger.info("Decision Engine stopped.")
