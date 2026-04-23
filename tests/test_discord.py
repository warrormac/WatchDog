import aiohttp
import asyncio
from datetime import datetime

async def test():
    # PASTE YOUR WEBHOOK URL HERE
    url = "https://discord.com/api/webhooks/1496487052127244400/THa-e2TLnLAKLZ-yl_RR613yNevQ39S5Qbo3t7B5I6zR03HY4n7dM2CmbOs8eSPDPF-Z"
    
    payload = {
        "embeds": [{
            "title": "🧪 SYSTEM TEST: Watchdog Online",
            "color": 0x3498db, # Blue for test
            "fields": [
                {"name": "Status", "value": "Connection Successful", "inline": True},
                {"name": "Time", "value": datetime.now().strftime('%H:%M:%S'), "inline": True}
            ],
            "footer": {"text": "Discord Integration Test"}
        }]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status in [200, 204]:
                print("✅ SUCCESS: Check your Discord channel!")
            else:
                print(f"❌ FAILED: Status {response.status}")

asyncio.run(test())