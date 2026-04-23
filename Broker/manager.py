import os
import sys
import yaml
import time
import logging
import asyncio
import aiohttp
import json
from datetime import datetime

# Allow finding Vault and config folders
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Vault.db import Database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BROKER")

class BrokerService:
    def __init__(self):
        # 1. Load Configuration
        with open("config/master.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        
        # 2. Database and Portfolio Paths
        self.db_path = self.config["vault"]["database_path"]
        self.pf_path = self.config["vault"].get("portfolio_path", "crypto_pool/portfolio.json")
        self.db = Database(db_path=self.db_path)
        
        # 3. Strategy Targets
        target_cfg = self.config.get("broker", {}).get("targets", {})
        self.targets = {
            "profit": target_cfg.get("profit_pct", 6.0) / 100,
            "loss": target_cfg.get("stop_loss_pct", 2.0) / 100,
            "high_conf": target_cfg.get("high_confidence_threshold", 0.85),
            "min_conf": self.config["present"].get("signal_threshold", 0.55)
        }

        # 4. Notification Settings
        notify_cfg = self.config.get("broker", {}).get("notifications", {})
        self.discord_url = notify_cfg.get("discord_webhook_url")
        self.alert_cooldown = notify_cfg.get("cooldown_seconds", 900)
        self.last_alert_times = {}

    def load_portfolio(self):
        """Loads current USD and coin holdings."""
        if os.path.exists(self.pf_path):
            with open(self.pf_path, "r") as f:
                return json.load(f)
        return {"USD": 100.0, "total_earnings_usd": 0.0, "positions": {}}

    def get_strategic_advice(self, symbol, current_price, oracle_direction, oracle_confidence, portfolio):
        """Calculates profit/loss and generates advice."""
        pos = portfolio["positions"].get(symbol, {"amount": 0.0, "cost_basis": 0.0})
        
        if pos["amount"] > 0:
            entry_price = pos.get("cost_basis", pos.get("cost", 0.0))
            if entry_price == 0: return None
            
            change = (current_price - entry_price) / entry_price
            
            if change >= self.targets["profit"]:
                if oracle_direction == "long" and oracle_confidence >= self.targets["high_conf"]:
                    return f"🚀 *PREDICTION: CONTINUED GROWTH*\nTarget hit (+{change*100:.2f}%), Oracle is very confident. HOLD!"
                return f"💰 *PREDICTION: REVERSAL LIKELY*\nTarget hit (+{change*100:.2f}%). Oracle cooling. SELL NOW."
            
            elif change <= -self.targets["loss"]:
                return f"⚠️ *PREDICTION: FURTHER DROP*\nStop loss hit (-{change*100:.2f}%). EXIT POSITION."
        
        elif oracle_direction == "long" and oracle_confidence >= self.targets["min_conf"]:
            return f"🚀 *PREDICTION: BUY OPPORTUNITY*\nOracle detects strong entry setup ({oracle_confidence:.2f})."
        
        return None

    async def send_discord(self, symbol, advice, confidence, price, warning):
        """Sends a color-coded embed to Discord."""
        if not self.discord_url: return False
        
        # Green for Buy/Growth, Red for Sell/Warning
        color = 0x2ecc71 if "BUY" in advice or "GROWTH" in advice else 0xe74c3c
        
        payload = {
            "embeds": [{
                "title": f"🛡️ WATCHDOG ALERT: {symbol}",
                "color": color,
                "fields": [
                    {"name": "🧠 Confidence", "value": f"{confidence:.2f}", "inline": True},
                    {"name": "🎯 Market Price", "value": f"${price:,.4f}", "inline": True},
                    {"name": "🔍 DEEP ANALYZE", "value": warning, "inline": False},
                    {"name": "📢 STRATEGY", "value": advice, "inline": False}
                ],
                "footer": {"text": "Watchdog Trading Sentinel"},
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.discord_url, json=payload) as response:
                return response.status in [200, 204]

    async def process_signals(self):
        """Main loop: Fetches signals and alerts via Discord."""
        new_signals = self.db.get_unprocessed_signals()
        if not new_signals: return

        portfolio = self.load_portfolio()
        for s in new_signals:
            advice = self.get_strategic_advice(s['symbol'], s['price'], s['direction'], s['confidence'], portfolio)
            if not advice:
                self.db.mark_signal_processed(s['id'])
                continue

            # Cooldown check
            last_time = self.last_alert_times.get(s['symbol'], 0)
            if time.time() - last_time < self.alert_cooldown:
                self.db.mark_signal_processed(s['id'])
                continue

            success = await self.send_discord(s['symbol'], advice, s['confidence'], s['price'], s.get('warning', 'None'))
            self.db.mark_signal_processed(s['id']) # Always mark processed to prevent loops
            
            if success:
                self.last_alert_times[s['symbol']] = time.time()
                logger.info(f"✅ Discord alert sent for {s['symbol']}")
            
            await asyncio.sleep(2) # Prevent API rate limits

    async def run_forever(self):
        logger.info(f"Broker Watchdog active. Target: {self.targets['profit']*100}% Profit / Stop: {self.targets['loss']*100}% Loss.")
        while True:
            await self.process_signals()
            await asyncio.sleep(60)

if __name__ == "__main__":
    broker = BrokerService()
    asyncio.run(broker.run_forever())