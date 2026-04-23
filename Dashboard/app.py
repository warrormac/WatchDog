import streamlit as st # type: ignore
import json
import pandas as pd # type: ignore
import sqlite3
import requests   # type: ignore
import os
import time
from datetime import datetime

# --- CONFIG & PATHS ---
PF_PATH = "crypto_pool/portfolio.json"
DB_PATH = "Vault/cryptobot.db"

st.set_page_config(
    page_title="Watchdog Command Center", 
    page_icon="🛡️", 
    layout="wide"
)

# --- DATA HELPERS ---
def load_portfolio():
    if os.path.exists(PF_PATH):
        try:
            with open(PF_PATH, "r") as f:
                return json.load(f)
        except:  # noqa: E722
            pass
    return {"USD": 100.0, "positions": {}}

def get_live_prices(symbols):
    prices = {}
    if not symbols: 
        return prices
    try:
        url = "https://api.binance.com/api/3/ticker/price"
        resp = requests.get(url, timeout=5).json()
        ticker_map = {item['symbol']: float(item['price']) for item in resp}
        for sym in symbols:
            prices[sym] = ticker_map.get(sym, 0.0)
    except Exception as e:
        st.sidebar.error(f"Binance Link Error: {e}")
    return prices

def get_latest_signals():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame(columns=['symbol', 'direction', 'price', 'confidence', 'ts'])
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT symbol, direction, price, confidence, ts FROM signals ORDER BY id DESC LIMIT 10", 
            conn
        )
    except:  # noqa: E722
        df = pd.DataFrame(columns=['symbol', 'direction', 'price', 'confidence', 'ts'])
    finally:
        conn.close()
    return df

# --- DASHBOARD LOGIC ---

portfolio = load_portfolio()
held_symbols = list(portfolio["positions"].keys())
watch_symbols = held_symbols + ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
live_prices = get_live_prices(watch_symbols)

cash = portfolio["USD"]
holdings_value = 0
positions_list = []

for sym, data in portfolio["positions"].items():
    current_price = live_prices.get(sym, 0.0)
    if current_price == 0:
        current_price = data['cost']
        
    val = data['amount'] * current_price
    holdings_value += val
    
    pnl_usd = val - (data['amount'] * data['cost'])
    pnl_pct = ((current_price - data['cost']) / data['cost']) * 100
    
    # NEW RESULT LOGIC: Neutral zone for $0.00 moves
    if pnl_pct > 0.01:
        result_emoji = "🟢 PROFIT"
    elif pnl_pct < -0.01:
        result_emoji = "🔴 LOSS"
    else:
        result_emoji = "🟡 EVEN"
    
    positions_list.append({
        "Symbol": sym,
        "Amount": data['amount'],
        "Entry Price": f"${data['cost']:.4f}",
        "Current Price": f"${current_price:.4f}",
        "Total Value": f"${val:.2f}",
        "PnL ($)": f"{pnl_usd:+.2f}",
        "PnL (%)": f"{pnl_pct:+.2f}%",
        "Result": result_emoji
    })

total_equity = cash + holdings_value
total_pnl = total_equity - 100.0

# --- UI RENDERING ---

st.title("🛡️ Watchdog Command Center")
st.caption(f"Last Heartbeat: {datetime.now().strftime('%H:%M:%S')} | Refresh: 60s")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Equity", f"${total_equity:.2f}", f"{total_pnl:+.2f}$")
m2.metric("Available Cash", f"${cash:.2f}")
m3.metric("Holdings Value", f"${holdings_value:.2f}")
m4.metric("Active Trades", len(positions_list))

st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("📦 My Wallet")
    if positions_list:
        df_pos = pd.DataFrame(positions_list)
        # UPDATED: width='stretch' replaces use_container_width=True
        st.dataframe(df_pos, width='stretch', hide_index=True)
    else:
        st.info("Wallet empty. Waiting for entry signal...")

with col_right:
    st.subheader("🧠 Oracle Intelligence (Flags)")
    signals_df = get_latest_signals()
    
    if not signals_df.empty:
        def style_signals(row):
            own_it = row['symbol'] in portfolio["positions"]
            if row['direction'] == 'long' and not own_it:
                return ['background-color: #28a745; color: white'] * len(row)
            if row['direction'] == 'short' and own_it:
                return ['background-color: #dc3545; color: white'] * len(row)
            return [''] * len(row)

        # UPDATED: width='stretch'
        st.dataframe(
            signals_df.style.apply(style_signals, axis=1),
            width='stretch',
            hide_index=True
        )
    else:
        st.warning("No signals found in the Vault. Check Terminal 2 (Oracle).")

st.divider()
st.info("💡 **Active Trading Tip:** Green = Buy Signal | Red = Sell Signal")

# Refresh logic
time.sleep(60)
st.rerun()