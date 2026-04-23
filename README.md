# 🛡️ Crypto Watchdog

An adaptive, multi-service trading bot architecture designed to filter market noise through deep technical analysis and strategic portfolio management.

## Setup

1. Create virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate virtual environment:
   - Windows: `.\.venv\Scripts\activate`
   - Unix: `source .venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
Update config/master.yaml with your API keys and Discord Webhook:

   ```
   broker:
   targets:
      profit_pct: 6.0
      stop_loss_pct: 2.0
   notifications:
      discord_webhook_url: "YOUR_URL_HERE"

   ```

## Execution
Run each service in a separate terminal to keep the Watchdog active:

   ```
   python Past/historian.py  # Sync History
   python Present/oracle.py    # Listen for Signals
   python Broker/manager.py    # Send Alerts

   ```