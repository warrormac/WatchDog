# CryptoBot

Automated cryptocurrency trading assistant.

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

## Structure

- `config/`: Configuration files for symbols, exchange keys, and strategy parameters.
- `cryptobot/`: Core source code.
  - `data/`: WebSocket feed, data normalization, and buffering.
  - `analysis/`: Indicator calculation and pattern recognition.
  - `risk/`: Position sizing and risk management guards.
  - `decision/`: Core engine that generates buy/sell/hold signals.
  - `execution/`: Order placement (paper and live).
  - `notify/`: Telegram notifications.
  - `storage/`: SQLite database logging.
  - `backtest/`: Historical data replay.
- `scripts/`: Entry point scripts.
- `tests/`: Unit and integration tests.
