import asyncio
import logging
from typing import Dict, Any
from cryptobot.analysis.scorer import FinalScore
from datetime import datetime

logger = logging.getLogger(__name__)

class ConsoleNotifier:
    """
    Consumes signals from the output queue and prints formatted alerts to the console.
    """
    
    def __init__(self, settings: Dict[str, Any]):
        self.output_queue = asyncio.Queue()
        self.is_running = False

    async def start(self):
        self.is_running = True
        logger.info("Console Notifier started.")
        
        while self.is_running:
            try:
                signal: FinalScore = await self.output_queue.get()
                if signal:
                    self._print_signal(signal)
                self.output_queue.task_done()
            except Exception as e:
                logger.error(f"Error in Console Notifier: {e}", exc_info=True)
                await asyncio.sleep(1)

    def _print_signal(self, signal: FinalScore):
        """Prints a nicely formatted block to the terminal."""
        # Use emojis for quick visual cues
        icon = "🟢" if signal.direction == "long" else "🔴"
        direction = "BUY" if signal.direction == "long" else "SELL"
        timestamp = datetime.fromtimestamp(signal.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        
        # print("\n" + "="*40)
        # print(f"{icon}  {direction}  {signal.symbol} @ {timestamp}")
        # print("="*40)
        # print(f"Confidence : {signal.confidence:.2f}")
        
        # if signal.patterns:
        #     print(f"Patterns   : {', '.join(signal.patterns)}")
            
        # if signal.reasons:
        #     print("\nConfluence reasons:")
        #     for reason in signal.reasons[:10]: # Limit for brevity
        #         print(f" - {reason}")
        # print("="*40 + "\n")

    def stop(self):
        self.is_running = False
        logger.info("Console Notifier stopped.")
