# CryptoBot — Developer Documentation

## Project overview

CryptoBot is a signal-only cryptocurrency trading assistant. It connects to public exchange APIs to fetch real-time candlestick data, identifies patterns and indicator-based setups, and prints BUY / SELL / HOLD signals to the console. The goal is to provide a "second pair of eyes" for manual traders without requiring any account linking, API keys, or automated trade execution.

---

## Repository layout

```
cryptobot/
├── config/
│   ├── settings.yaml          # coins, timeframes, exchange selection
│   └── strategy.yaml          # pattern weights, indicator params
├── cryptobot/
│   ├── __init__.py
│   ├── data/
│   │   ├── feed.py            # Public WebSocket client (no API keys)
│   │   ├── normaliser.py      # unified OHLCV tick format
│   │   └── buffer.py          # ring buffer for live + historical bars
│   ├── analysis/
│   │   ├── patterns.py        # candlestick pattern detector
│   │   ├── indicators.py      # RSI, MACD, EMA, Bollinger Bands, volume
│   │   ├── multi_tf.py        # multi-timeframe confluence checker
│   │   └── scorer.py          # weighted signal combiner
│   ├── decision/
│   │   └── engine.py          # produces final BUY / SELL / HOLD signals
│   ├── notify/
│   │   └── console.py         # formatted console alerts and logging
│   ├── storage/
│   │   └── db.py              # SQLite logger + CSV exporter
│   └── backtest/
│       └── runner.py          # replay historical data through the pipeline
├── tests/
├── scripts/
│   └── run.py                 # main entry point
├── requirements.txt
└── README.md
```

---

## Technology stack

| Layer | Library | Why |
|---|---|---|
| Exchange connectivity | `ccxt` | Unified API for public data (no keys required) |
| Candlestick patterns | `pandas-ta-classic` | Indicator and pattern detection compatible with Python 3.10 |
| Data frames | `pandas`, `numpy` | OHLCV manipulation and maths |
| Async runtime | `asyncio` + `websockets` | Non-blocking feed ingestion |
| Configuration | `PyYAML` | Human-editable settings |
| Storage | `sqlite3` | Audit trail for signals |
| Testing | `pytest` + `pytest-asyncio` | Verification of patterns and logic |

---

## Configuration reference

**`config/settings.yaml`**

```yaml
exchanges:
  - id: binance  # Uses public data only

symbols:
  - BTC/USDT
  - ETH/USDT
  - SOL/USDT

timeframes: [1m, 5m, 15m, 1h, 4h]

notifications:
  mode: console  # Just prints to terminal
```

---

## Development roadmap

### Phase 1 — Foundation
- [x] Project scaffold and virtual environment
- [x] `settings.yaml` and `strategy.yaml` (No API keys)
- [x] `ExchangeFeed` using public Binance WebSocket
- [x] `RingBuffer` and OHLCV normaliser
- [x] Unit tests for normaliser and buffer

### Phase 2 — Analysis core
- [x] Single-candle pattern functions + tests
- [x] Multi-candle pattern functions + tests
- [ ] Indicator computation via `pandas-ta-classic`
- [ ] Multi-timeframe confluence checker
- [ ] Signal scorer with weight config

### Phase 3 — Decision and Output
- [ ] Decision engine for signal generation
- [ ] Console notification formatting
- [ ] SQLite logger for signals audit

### Phase 4 — Validation
- [ ] Backtesting runner
- [ ] Signal validation against historical data
