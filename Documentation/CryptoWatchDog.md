# Crypto Watchdog

Date Apr 20, 2026

Owner [warrormac](mailto:warrormac@gmail.com)

# Project Introduction 

The **Crypto Watchdog** is a professional-grade algorithmic trading assistant that bridges the gap between raw market data and actionable profit. Operating on the **1-minute and 5-minute timeframes**, it is built to be "active" while protecting your **$N** starting capital through strict risk management and predictive logic. 

## Objectives

* **Monitors 24/7:** Scans multiple coin pairs (BTC, ETH, ADA) without fatigue. 

* **Detects Patterns:** Uses technical indicators (RSI, EMA) and candle patterns to find high-probability entries. 

* **Predicts Trends:** Analyzes market conviction to tell you whether to "Sell Now" or "Let it Ride" for more profit. 

* **Automates Communication:** Sends real-time strategic alerts to your phone via WhatsApp. 

## System Architecture (The Folders) 

| Folder | Name  | Description | Execute |
| :---- | :---- | :---- | :---- |
| Past  | Historian  | Fetches thousands of historical candles to give the bot "memory" of past price action.  | python Past/historian.py |
| Present  | Oracle  | The "Live Brain." It connects to Binance WebSockets to analyze every single 1-minute candle as it closes.  | python Present/oracle.py |
| Broker  | Manager  | The "Watchdog." It monitors your actual portfolio, checks targets (6% gain / 2% loss), and sends phone alerts.  | python Broker/manager.py |
| Vault  | Database  | The "Central Intelligence." Stores every candle, every signal, and your current portfolio balance.  | python log\_trade.py  |

## The Pipeline Flow 

The project operates as a continuous loop, transforming raw price movements into notifications on your phone:

1. **Ingestion:** The **Historian** fills the Vault with past data so the bot isn't trading "blind".  
2. **Analysis:** The **Oracle** receives live prices. It calculates indicators and "scores" the market. If the score is high (e.g., \>0.55), it saves a **Signal** to the Vault.  
3. **Strategy:** The **Broker** polls the Vault every 60 seconds. It compares the new Signal against your **Portfolio**.  
4. **Action:** \* **If you own nothing:** It predicts a "BUY OPPORTUNITY".  
   * **If you own a coin:** It calculates your PnL. If your 6% target is hit, it predicts "REVERSAL" or "GROWTH" and sends a WhatsApp.

# Pipeline Flow

The **Crypto Watchdog** operates on a decoupled "Pseudo-Microservice" architecture where each module is an independent worker. Instead of communicating via complex APIs, these services use the **Vault (Database)** as a "Shared State" to pass information.

1. ### The Pipeline Flow: From Market to Mobile 

     
   The flow of data follows a linear path from the exchange to your phone, moving through five distinct stages:   
   

   ### Stage 0: The Historical Foundation (Past/Historian)

   Before a single live trade is considered, the **Historian** must build the "memory" of the bot.  
* **Lookback Requirement:** Technical indicators like RSI or EMA are mathematical averages; you cannot calculate a 14-period RSI with only one live candle. You need the previous 14 candles at a minimum.  
* **Deep Sync:** The Historian connects to the Binance REST API to fetch a massive block of data (defined as warmup\_candles: 10000 in your config).  
* **The "Warm-up":** On startup, the Oracle reads these 10,000 candles from the Vault to "warm up" its memory buffers, ensuring that its very first live calculation is mathematically accurate.

  ### **Stage A: Live Ingestion (Present/Oracle)**

* The **Oracle** establishes a high-speed WebSocket connection to the Binance stream.  
* It listens for 1-minute candle closures specifically for the symbols listed in your master.yaml.  
* Every closed candle is normalized and immediately saved to the **Vault** for historical reference.

  ### **Stage B: Scoring & Intelligence (Present/Oracle)**

* The Oracle passes the live data through the SignalScorer.  
* It calculates indicators like **RSI** and **EMA** defined in your configuration.  
* If the resulting confidence score meets your signal\_threshold (e.g., 0.55), a new Signal row is inserted into the database.

  ### **Stage C: Central Storage (Vault)**

* The SQLite database acts as the single source of truth.  
* It stores both "Market Data" (candles) and "Intelligence Data" (unprocessed signals).

  ### **Stage D: Strategic Evaluation (Broker/Manager)**

* The **Broker** polls the database every 60 seconds looking for signals where processed \= 0\.  
* It loads your current portfolio.json to see what you actually own.  
* It runs the **Prediction Logic**: comparing the signal against your entry price to decide if it's a "Buy Opportunity," a "Reversal," or "Continued Growth".

  ### **Stage E: Alerting (Broker/Manager)**

* If the strategy requires action, the Broker formats a WhatsApp message.  
* It checks the alert\_cooldown (900 seconds) to ensure you aren't spammed with too many messages.  
* Once sent, it marks that signal as processed \= 1 so it is never analyzed again.


2. ### Microservices Architecture

    Although this project runs on a single machine, it is designed as a set of **Micro-Workers**. This means you can stop, update, and restart any single part without crashing the others.

   #### The "Shared State" Pattern

   In standard microservices, services talk via HTTP requests. In this bot, we use the **Database-as-a-Message-Bus**:

* **The Oracle** doesn't care if the Broker is running; it just keeps writing signals to the DB.  
* **The Broker** doesn't care where the signals come from; it just watches the DB for new rows.

#### 	

#### Service Breakdown 

| Service  | Independent Lifecycle  | Communication Method  |
| :---- | :---- | :---- |
| Historian  | Runs periodically (Backfills past data).  | Writes to cryptobot.db.  |
| Oracle  | Constant connection (Live Brain).  | Writes to cryptobot.db.  |
| Broker  | Interval polling (Strategy/Alerts).  | Reads cryptobot.db & portfolio.json.  |
| Dashboard  | Web-based view (User Interface).  | The "Central Intelligence." Stores every candle, Reads both DB and JSON files. signal, and your current portfolio balance.  |

### Flow of Crypto Watchdog 

To understand the "flow" of the **Crypto Watchdog**, we must look at it as a relay race where the "baton" is the market data. The project moves through three distinct phases: **Initialization**, **The Live Loop**, and **The Strategic Action**. 

### Phase 1: Initialization (The "Warm-up")  **python Past/[historian.py](http://historian.py)**

Before the bot can make decisions, it must establish a context using historical data.

1. **Historian Seed:** The **Historian** fetches 10,000 candles from the Binance API and stores them in the `cryptobot.db` file.  
2. **Oracle Memory:** Upon startup, the **Oracle** runs its `warm_up` function, loading those candles from the database into memory-based "Ring Buffers".  
3. **Indicator Readiness:** By having these 10,000 candles ready, the bot can instantly calculate long-term Moving Averages and RSI values without waiting for new live data.

### Phase 2: The Live Loop (Observation & Intelligence)  **python Present/[oracle.py](http://oracle.py)**

Once initialized, the **Oracle** enters a continuous, high-speed loop driven by WebSockets.

1. **WebSocket Ingestion:** The Oracle listens to the Binance live stream for 1-minute and 5-minute candle updates.  
2. **Candle Closure:** When a candle "closes" (the minute ends), the Oracle performs two tasks:  
   * **Persistence:** It saves the new candle to the Vault to keep history up to date.  
   * **Buffer Update:** It pushes the candle into the memory buffer for immediate analysis.  
3. **Signal Scoring:** The SignalScorer analyzes the updated buffers. If the **Confidence Score** (based on indicator weights in master.yaml) exceeds the signal\_threshold (0.55), a new row is written to the **Signals Table** in the Vault.

### Phase 3: The Strategic Action (Broker & Alerting)  **python Broker/[manager.py](http://manager.py)**

The **Broker** operates on a separate, 60-second heartbeat, acting as the decision-maker.

1. **Vault Polling:** The Broker queries the database for any rows in the signals table where processed \= 0\.  
2. **Portfolio Sync:** It loads your portfolio.json to see if you currently own the coin mentioned in the signal.  
3. **Strategy Check:**  
   * **Profit/Loss:** It calculates the current PnL of your holdings against the profit\_pct and stop\_loss\_pct targets in master.yaml.  
   * **Prediction:** It uses the Oracle's confidence to predict if a coin will continue growing or if it is time to sell.  
4. **Notification:** If a move is required, it formats a WhatsApp message and sends it via CallMeBot, provided the 15-minute alert\_cooldown has passed.  
5. **Clean-up:** Once evaluated, the signal is marked as processed \= 1 so it is never analyzed again.

# Project Elements

## Past (The Historian)

The **Past** folder is the foundation of the bot's intelligence. It houses the **Historian Service**, which is responsible for building and maintaining the "memory" of the entire system. Without this module, the bot would have no context for market trends or technical indicators. 

### 1\. Core Responsibility 

The Historian is in charge of **Historical Data Synchronization**. It ensures that the **Vault (Database)** is seeded with enough price action data (candles) to allow the **Oracle** to calculate accurate technical indicators, such as RSI or Moving Averages, the moment the bot starts. 

### 2\. How it Works 

The Historian operates as an independent background worker that follows a specific logic path:

* **Initialization:** Upon startup, the service loads the master.yaml configuration to identify which symbols and timeframes need tracking.  
* **Database Connection:** it establishes a link to the central SQLite database in the Vault.  
* **The "Smart Sync" Logic:** \* Instead of downloading the same data every time, the Historian checks the Vault to find the **latest timestamp** saved for each coin/timeframe pair.  
  * It then builds a request to the Binance REST API, asking only for candles that have occurred **after** that specific timestamp.  
* **Data Normalization:** Raw data received from Binance is formatted into a standardized "normalized" structure (timestamp, open, high, low, close, volume) before being committed to the database.  
* **Rate Limiting:** The service includes a "gentle pause" between requests to ensure the bot does not get banned by Binance for making too many API calls too quickly.

### 3\. Key Technical Specifications 

The behavior of the Historian is governed entirely by the master.yaml file, removing the need for manual code changes: 

| Feature  | Description | Config Key  |
| :---- | :---- | :---- |
| Warm-up Limit  | Number of historical candles fetched to start the "memory" (e.g., 10,000).  | past: warmup\_candles  |
| Sync Interval  | How often the service wakes up to perform a deep historical backup.  | past: sync\_interval\_hours  |
| API Endpoint  | The professional-grade REST URL used to communicate with Binance.  | past: exchange\_api  |

### 4\. Why This Element is Critical

In active trading (1m/5m), price spikes are common. The Historian provides the **long-term perspective**. By maintaining a history of up to 10,000 candles, the bot can determine if a 1-minute price jump is a genuine breakout or just noise in a larger downward trend. This historical context is what allowed your bot to confidently identify the **8.16% ADA gain** while ignoring smaller, riskier movements.

## Present (The Oracle) 

The **Present** folder is the active "Command Center" of the bot. It houses the **Oracle Service**, a high-speed, real-time analysis engine that converts live market movements into actionable trading signals. While the Historian looks at what *happened*, the Oracle is focused entirely on what is happening *now*. 

### **1\. Core Responsibility**

The Oracle is in charge of **Live Market Intelligence**. It maintains a persistent, low-latency connection to the exchange to monitor every single price tick. Its primary goal is to identify specific mathematical patterns (Signals) the moment a candle closes and broadcast those findings to the **Vault** for the Broker to act upon.

### **2\. How it Works**

The Oracle operates as a sophisticated event-driven service with a multi-step processing pipeline:

* **WebSocket Ingestion:** It establishes a "Listen Key" with the Binance stream, subscribing to specific @kline streams for every symbol and timeframe defined in your configuration.  
* **Memory Buffering:** To analyze trends, the Oracle uses a **RingBuffer**. This is an in-memory "sliding window" that holds the last few hundred candles (seeded initially by the Historian), allowing for instant calculations without constant database queries.  
* **Normalization:** It uses a normalizer to translate the raw, messy JSON data from Binance into a clean format the bot understands.  
* **Live Analysis:** \* **Indicator Injection:** The moment a 1-minute candle closes, the Oracle injects it into the buffer and runs add\_indicators to calculate RSI, EMA, and other technical metrics.  
  * **Pattern Scoring:** The SignalScorer then evaluates the combined data. It assigns a "Confidence Score" to the current market state.  
* **Signal Persistence:** If the pattern is strong enough to meet the signal\_threshold (e.g., 0.55), the Oracle writes the signal—including the direction (LONG/SHORT), price, and confidence—directly into the Vault.

### **3\. Key Technical Specifications**

The Oracle's behavior is tuned via the **master.yaml** to match your "Active Week" trading style:

| Feature  | Description | Config Key  |
| :---- | :---- | :---- |
| WebSocket URL  | The high-speed address used for live Binance data.  | present: exchange\_ws  |
| Confidence Bar  | The minimum score (0.0 to 1.0) required to trigger a signal.  | present: signal\_threshold  |
| Strategy Weights  | How much importance the bot gives to different timeframes (e.g., 1m vs 1h).  | present: weights  |

### **4\. Why This Element is Critical**

The Oracle is the only part of the system that "sees" the live market. It acts as a filter, removing the emotional noise of the 1-minute charts and only saving data that matches a high-probability winning setup.

Without the Oracle, the system would have no way to detect the sudden 1.00 confidence "Moon Shot" patterns that lead to trades like your **8.16% ADA gain**. It ensures that you are only alerted when the math is in your favor, allowing you to be "very active" without being "reckless."

## Broker (The Watchdog) 

The **Broker** folder is the project's "Disciplined Executioner." It houses the **Manager Service**, which acts as your 24/7 account manager. While the Oracle finds the opportunities, the Broker decides if they are worth your money and tells you exactly when to get out to protect your $100 capital. 

### **1\. Core Responsibility**

The Broker is in charge of **Strategic Risk Management and Alerting**. It sits between the Oracle's mathematical signals and your real-world wallet. Its primary job is to monitor active positions, calculate real-time profit/loss (PnL), and send high-priority strategic advice to your phone via WhatsApp.

### **2\. How it Works**

The Broker operates on a steady 60-second "heartbeat," performing a recursive check of your entire financial state:

* **Portfolio Sync:** It loads the portfolio.json file from the Vault to see exactly how much USD you have and which coins you are currently holding.  
* **Vault Polling:** It queries the SQLite database for new, "unprocessed" signals generated by the Oracle.  
* **Strategic Evaluation:** For every signal, the Broker runs a comparative analysis:  
  * **The Profit Target:** If a coin you own has risen by your target amount (e.g., 6%), it prepares a "SELL" alert.  
  * **The Stop Loss:** If a coin drops below your safety threshold (e.g., 2%), it prepares an emergency "EXIT" alert to prevent further loss.  
* **Predictive Logic:** Instead of just looking at numbers, it looks at the **Oracle’s Confidence**. If you are in profit but the Oracle is 90% sure the coin will keep growing, the Broker predicts "CONTINUED GROWTH" and advises you to hold for more profit.  
* **Rate-Limited Alerting:** It formats a professional alert and sends it via the CallMeBot API, ensuring it respects the 15-minute cooldown\_seconds so your WhatsApp isn't flooded.

### **3\. Key Technical Specifications**

All of the Broker’s "discipline" is defined in the master.yaml, making it easy to change your strategy without touching the code:

| Feature  | Description | Config Key  |
| :---- | :---- | :---- |
| Profit Goal  | The percentage gain where the bot tells you to secure profits (e.g., 6.0%).  | broker: targets: profit\_pct  |
| Safety Net  | The maximum loss allowed before the bot tells you to cut ties (e.g., 2.0%).  | broker: targets: stop\_loss\_pct  |
| Notification Gap  | The time in seconds to wait between phone alerts (e.g., 900s / 15m).  | broker: notifications: cooldown\_seconds  |
| Conviction Bar  | The Oracle confidence score required to suggest a "Let it Ride" hold.  | broker: targets: high\_confidence\_threshold  |

### **4\. Why This Element is Critical**

The Broker is what makes this project a "Watchdog" rather than just a chart viewer. It removes the "Greed" and "Fear" from trading.

It was the Broker that monitored your ADA position and sent the alert saying **"TARGET HIT\! Advice: SELL"** which allowed you to bank that **8.16% profit**. It ensures that while you are "very active" in the 1-minute and 5-minute markets, you are always trading with a calculated exit plan.

## Vault (The Central Intelligence) 

The **Vault** is the project's "Shared Memory" and the single source of truth for the entire system. It is not a running service like the Oracle or Broker; instead, it is the persistent storage layer that allows all independent modules to communicate seamlessly without ever talking to each other directly.

### **1\. Core Responsibility**

The Vault is in charge of **Data Integrity and State Management**. It ensures that the current market price (from the Historian/Oracle), the detected trade opportunities (Signals), and your actual wallet balance (Portfolio) are always synchronized across every screen and service.

### **2\. The Two Pillars of the Vault**

The Vault manages information using two different storage formats, each optimized for a specific type of data:

#### **A. The SQLite Database (**cryptobot.db**)**

This is the "Big Brain" where large volumes of time-series data are stored.

* **Candles Table:** Stores thousands of historical and live price points (Open, High, Low, Close, Volume) used for technical analysis.  
* **Signals Table:** Acts as the "Inbox" for the Broker. It stores every high-confidence pattern detected by the Oracle, including the direction, entry price, and confidence score.  
* **Processed Flag:** It tracks which signals have already been sent to your phone so you never receive the same alert twice.

#### **B. The Portfolio Ledger (**portfolio.json**)**

This is a lightweight JSON file that acts as your "Personal Bank".

* **USD Balance:** Tracks your available cash for trading.  
* **Active Positions:** Keeps a record of exactly how much of a coin you bought and at what price (the "Cost Basis").  
* **Manual Bridge:** This file is updated by the log\_trade.py utility whenever you make a move on the exchange.

### **3\. How it Enables Microservices**

The Vault is the reason the bot can function as a set of microservices:

* **Decoupling:** The **Oracle** writes to the database and then forgets about it. It doesn't need to know if the Broker is even turned on.  
* **Asynchronous Flow:** The **Broker** wakes up every 60 seconds and checks the "Signals" table. It doesn't need to know how the Oracle calculated the signal; it only cares that the signal exists in the Vault.  
* **UI Sync:** The **Dashboard** reads from both the DB and JSON files to show you your live status.

### **4\. Key Technical Specifications**

The location and behavior of the Vault are defined in the `vault` section of your master configuration:

| Element | Description | Config Key  |
| :---- | :---- | :---- |
| Database Path  | The exact location of the SQLite file.  | vault: database\_path  |
| Portfolio Path  | The exact location of the JSON ledger.  | vault: portfolio\_path  |
| Auto-Backup  | Ensures a copy of the database is made to prevent data loss.  | vault: auto\_backup  |

### **5\. Why This Element is Critical**

Without the Vault, the system would be a collection of "blind" scripts. It provides the continuity needed for long-term growth. Because the Vault stored your entry price for ADA ($0.2401) in portfolio.json, the Broker was able to calculate that you were up **8.16%** and tell you exactly when to take your profit.

## **log\_trade.py (The Ledger Bridge)**

While the **Oracle** and **Broker** handle the automated analysis, the **log\_trade.py** utility is the manual bridge between your real-world exchange (Binance) and the bot's internal logic. It ensures that the bot's "Digital Wallet" remains perfectly synced with your actual coins and cash.

---

### 1\. Core Responsibility

The log\_trade.py utility is in charge of **Portfolio Reconciliation**. Because the bot does not have permission to execute trades on your behalf (for safety), it relies on this script to know exactly what you bought, how much you spent, and the price you paid.

### 2\. How it Works

This utility acts as a simple, interactive CLI (Command Line Interface) that performs the following steps:

* **Configuration Access:** It reads master.yaml to locate the portfolio\_path (usually crypto\_pool/portfolio.json).  
* **User Prompts:** It asks the user for four specific pieces of data:  
  * **Symbol:** The coin pair traded (e.g., ADAUSDT).  
  * **Action:** Whether you performed a buy or a sell.  
  * **Amount:** The **quantity** of the coin (e.g., 40.0 ADA).  
  * **Price:** The exact price per coin from your exchange receipt (e.g., $0.2401).  
* Ledger Calculation:  
  * **On Buy:** It deducts the total cost ($Amount \\times Price$) from your available USD and adds the coin quantity to your positions.  
  * **On Sell:** It adds the proceeds to your USD balance and sets the coin quantity to 0.0.  
* **Vault Commit:** The script overwrites the portfolio.json file with the updated math, instantly reflecting the changes on your **Dashboard** and in the **Broker's** logic.

---

### 3\. Why This Utility is Critical

Without log\_trade.py, the Broker would be "trading blind."

* Cost Basis Tracking: The Broker needs to know your "Entry Price" to calculate if you have hit your 6% profit target or 2% stop-loss.  
* Accurate Alerts: By logging your ADAUSDT trade at $0.2401, you allowed the Broker to monitor the live price and send you the alert that resulted in your 8.16% profit.  
* Sanity Checking: It acts as a final manual check. By entering the coin quantity (e.g., 0.00013 BTC) rather than the USD value, you ensure the bot calculates your total equity correctly and avoids accounting errors.

