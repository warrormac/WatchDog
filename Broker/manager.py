import os
import sys
import yaml # type: ignore
import time
import logging
import asyncio
import aiohttp # type: ignore
import json
import sqlite3
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
        
        self.last_activity_time = time.time()
        self.heartbeat_interval = 15 * 60

    def load_portfolio(self):
        """Loads current USD and coin holdings."""
        if os.path.exists(self.pf_path):
            with open(self.pf_path, "r") as f:
                return json.load(f)
        return {"USD": 100.0, "total_earnings_usd": 0.0, "positions": {}}

    def get_strategic_advice(self, symbol, current_price, oracle_direction, oracle_confidence, warning, portfolio):
        """
        Lot-based Strategy Engine with a $5.00 Wallet Floor.
        """
        lots = portfolio["positions"].get(symbol, [])
        available_usd = portfolio.get("USD", 0)
        advice_list = []
        warning_upper = warning.upper() if warning else ""

        # --- 🔴 PART 1: SELLING & TACTICAL EXIT (Always runs, even if broke!) ---
        for i, lot in enumerate(lots):
            entry_price = lot.get("price", 0)
            if entry_price == 0: 
                continue
            change = (current_price - entry_price) / entry_price
            
            if change >= self.targets["profit"]:
                advice_list.append(f"🔥 Lot #{i+1} FULL TARGET (+{change*100:.2f}%). Advice: SELL NOW.")
            elif 0.03 <= change < self.targets["profit"]:
                if "RESISTANCE" in warning_upper or "OVEREXTENDED" in warning_upper or oracle_direction == "short":
                    advice_list.append(f"💎 Lot #{i+1} TACTICAL PROFIT (+{change*100:.2f}%). Wall detected. Advice: SELL EARLY.")
            elif change <= -self.targets["loss"]:
                advice_list.append(f"🛑 Lot #{i+1} STOP LOSS ({change*100:.2f}%). Advice: EXIT LOT.")

        if advice_list:
            return "\n".join(advice_list)

        # --- 🟢 PART 2: BUYING & DCA LOGIC ---
        
        # 🛡️ NEW: WALLET FLOOR GUARD
        # If balance is under $5, stop evaluating buys to save resources and Discord noise.
        if available_usd < 5.0:
            return None

        if oracle_direction == "long" and oracle_confidence >= self.targets.get("min_conf", 0.55):
            # We keep the $10 check here because Binance requires $10 to trade.
            min_entry_usd = 10.0
            
            if available_usd >= min_entry_usd:
                if len(lots) >= 3:
                    return f"🟠 HOLD: Oracle bullish ({oracle_confidence:.2f}), but max lots (3) reached for {symbol}."
                
                if len(lots) == 0:
                    return f"🚀 NEW POSITION: Oracle confident ({oracle_confidence:.2f}). Ammo: ${available_usd:.2f}"
                else:
                    return f"📈 DCA ADDITION: Oracle confident ({oracle_confidence:.2f}). Adding Lot #{len(lots)+1}. Ammo: ${available_usd:.2f}"
            else:
                # This only triggers if balance is between $5.00 and $9.99
                return f"❌ SKIP: Signal detected, but balance (${available_usd:.2f}) is below exchange minimum ($10)."

        return None

    async def send_discord(self, symbol, advice, confidence, price, warning):
        """
        Sends a high-visibility, tactical alert to Discord.
        Color-coded for Buy (Green), Sell (Red), Tactical Profit (Purple), or Hold (Yellow).
        """
        if not self.discord_url:
            logger.error("❌ Discord Error: No Webhook URL found in config!")
            return False
        
        # 1. Fetch current USD balance for the 'Available Ammo' display
        portfolio = self.load_portfolio()
        usd_balance = portfolio.get("USD", 0)
        advice_upper = advice.upper()
        
        # 2. Visual Categorization Logic
        # Priority 1: Tactical Profit (Purple)
        if "TACTICAL PROFIT" in advice_upper:
            action_header = "💎 TACTICAL PROFIT: SELL"
            color = 0x9b59b6  # Amethyst Purple
            
        # Priority 2: Buying / DCA (Green)
        elif any(x in advice_upper for x in ["BUY", "OPEN POSITION", "DCA ADDITION"]):
            action_header = "🟢 ACTION: BUY / LONG"
            color = 0x2ecc71  # Emerald Green
            
        # Priority 3: Full Sell / Exit (Red)
        elif any(x in advice_upper for x in ["SELL", "EXIT", "STOP LOSS", "DROP"]):
            action_header = "🔴 ACTION: SELL / EXIT"
            color = 0xe74c3c  # Alizarin Red
            
        # Priority 4: Standard Hold (Yellow)
        else:
            action_header = "🟠 ACTION: HOLD / WATCH"
            color = 0xf1c40f  # Sun Yellow

        # 3. Build the Professional Embed Payload
        payload = {
            "embeds": [{
                "title": f"{action_header} | {symbol}",
                "description": f"💰 **Market Price:** `${price:,.4f}`",
                "color": color,
                "fields": [
                    {
                        "name": "🎯 Strategy Verdict", 
                        "value": f"```yaml\n{advice}\n```", 
                        "inline": False
                    },
                    {
                        "name": "🧠 Oracle Confidence", 
                        "value": f"`{confidence:.2f}`", 
                        "inline": True
                    },
                    {
                        "name": "🔍 Deep Analyze", 
                        "value": f"**{warning if warning else 'Clean Scan'}**", 
                        "inline": True
                    },
                    {
                        "name": "💵 Available Ammo", 
                        "value": f"`${usd_balance:,.2f} USD`", 
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Watchdog Sentinel | Targets: {self.targets['profit']*100}% P / {self.targets['loss']*100}% L"
                },
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        # 4. Execute the delivery via aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.discord_url, json=payload) as response:
                    if response.status in [200, 204]:
                        return True
                    else:
                        logger.error(f"❌ Discord API Error: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Connection Error sending to Discord: {e}")
                return False

    async def process_signals(self):
        """
        Main engine: Fetches signals, applies strategy, and alerts Discord.
        Returns True if a message was successfully delivered (to reset heartbeat timer).
        """
        # 1. Pull any new signals the Oracle has saved to the Vault
        new_signals = self.db.get_unprocessed_signals()
        if not new_signals:
            return False

        logger.info(f"📬 Found {len(new_signals)} unprocessed signals. Analyzing...")
        
        # 2. Load the latest portfolio (List-based lots and USD balance)
        portfolio = self.load_portfolio()
        activity_detected = False

        for s in new_signals:
            # 3. Get Strategic Advice (Now passing the 'warning' string)
            # This triggers the 'Tactical Exit' logic if resistance/RSI warnings exist.
            advice = self.get_strategic_advice(
                s['symbol'], 
                s['price'], 
                s['direction'], 
                s['confidence'], 
                s.get('warning', ''), # Pass the Deep Analysis string
                portfolio
            )
            
            # 4. If Strategy returns None (Hold/Skip), just mark as done and move on
            if not advice:
                self.db.mark_signal_processed(s['id'])
                continue

            # 5. Cooldown Check: Avoid spamming the same coin in a short window
            last_time = self.last_alert_times.get(s['symbol'], 0)
            if time.time() - last_time < self.alert_cooldown:
                self.db.mark_signal_processed(s['id'])
                continue

            # 6. Strategy Accepted! Attempt to send the Discord Embed
            logger.info(f"   🚀 Strategy Accepted! Sending Discord alert for {s['symbol']}...")
            success = await self.send_discord(
                s['symbol'], 
                advice, 
                s['confidence'], 
                s['price'], 
                s.get('warning', '')
            )
            
            # 7. Always mark as processed to prevent infinite loops
            self.db.mark_signal_processed(s['id'])
            
            if success:
                # Update last alert time and signal that we were active
                self.last_alert_times[s['symbol']] = time.time()
                logger.info(f"   ✅ Discord alert delivered for {s['symbol']}.")
                activity_detected = True
            
            # Be kind to Discord's API rate limits
            await asyncio.sleep(1)

        return activity_detected
    
    async def send_heartbeat(self):
        """Sends a status update if no trade alerts have fired recently."""
        
        portfolio = self.load_portfolio()
        positions = portfolio.get("positions", {})
        
        status_lines = []
        
        # 1. Connect directly to the vault to get current prices
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for symbol, lots in positions.items():
                if not lots: continue
                
                # Get the most recent price seen by the Oracle
                cursor.execute(
                    "SELECT price FROM signals WHERE symbol = ? ORDER BY id DESC LIMIT 1", 
                    (symbol,)
                )
                row = cursor.fetchone()
                current_price = row[0] if row else 0
                
                if current_price == 0: continue
                
                # 2. Calculate P/L for this coin's holdings
                total_cost = sum(l['usd_value'] for l in lots)
                total_qty = sum(l['amount'] for l in lots)
                avg_price = total_cost / total_qty
                pnl_pct = ((current_price - avg_price) / avg_price) * 100
                
                # Emoji based on performance
                emoji = "📈" if pnl_pct >= 0 else "📉"
                status_lines.append(f"{emoji} **{symbol}**: `${current_price:,.4f}` ({pnl_pct:+.2f}%)")

            conn.close()
        except Exception as e:
            logger.error(f"❌ Heartbeat Price Check Failed: {e}")
            return

        if not status_lines:
            status_text = "No active positions. Monitoring for high-confidence entries..."
        else:
            status_text = "\n".join(status_lines)

        # 3. Send the Status Embed to Discord
        payload = {
            "embeds": [{
                "title": "💓 WATCHDOG HEARTBEAT: Active",
                "description": f"Market Status Report:\n\n{status_text}",
                "color": 0x3498db,  # Information Blue
                "fields": [
                    {"name": "💵 Available Ammo", "value": f"`${portfolio.get('USD', 0):,.2f} USD`", "inline": True},
                    {"name": "📈 Realized Profit", "value": f"`${portfolio.get('total_earnings_usd', 0):,.2f}`", "inline": True}
                ],
                "footer": {"text": f"Goal Progress: {((portfolio.get('USD',0) + sum(sum(l['usd_value'] for l in lots) for lots in positions.values() if lots)) / portfolio.get('financial_goal', 3000) * 100):.2f}% to Target"},
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.discord_url, json=payload) as response:
                    if response.status in [200, 204]:
                        logger.info("💓 Heartbeat delivered to Discord.")
            except Exception as e:
                logger.error(f"❌ Heartbeat Delivery Failed: {e}")

    async def run_forever(self):
        """Main loop with Startup Ping and Heartbeat timer."""
        logger.info(f"🛡️ Watchdog Broker active. Target: {self.targets['profit']*100}% P / {self.targets['loss']*100}% L.")
        
        # --- 🚀 NEW: STARTUP PING ---
        # This tells you IMMEDIATELY if Discord is connected when you start the bot.
        try:
            await self.send_discord("SYSTEM", "✅ Watchdog Broker is now ONLINE and monitoring.", 1.0, 0, "Startup Check")
            logger.info("🚀 Startup Ping sent to Discord.")
        except Exception as e:
            logger.error(f"❌ Failed to send Startup Ping: {e}")

        # TEMPORARY: Set to 2 minutes for testing (change back to 15 later)
        test_heartbeat = 10 * 60 
        
        while True:
            # 1. Check for signals (returns True if an alert was sent)
            alert_sent = await self.process_signals()
            
            # 2. Reset timer if an alert happened
            if alert_sent:
                self.last_activity_time = time.time()
                logger.info("⏱️ Activity detected. Heartbeat timer reset.")
            
            # 3. Check if it's time for a heartbeat
            elif time.time() - self.last_activity_time >= test_heartbeat:
                logger.info("💓 10 minutes of silence. Sending heartbeat...")
                await self.send_heartbeat()
                self.last_activity_time = time.time() 
            
            await asyncio.sleep(30) # Check every 30 seconds for better responsiveness

if __name__ == "__main__":
    broker = BrokerService()
    asyncio.run(broker.run_forever())