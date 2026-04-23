import json
import os
from datetime import datetime

PF_PATH = "crypto_pool/portfolio.json"

def load_portfolio():
    if os.path.exists(PF_PATH):
        with open(PF_PATH, "r") as f:
            return json.load(f)
    return {"USD": 100.0, "total_earnings_usd": 0.0, "positions": {}}

def save_portfolio(pf):
    with open(PF_PATH, "w") as f:
        json.dump(pf, f, indent=4)

def run_logger():
    pf = load_portfolio()
    print("\n" + "="*30)
    print("      🛡️ WATCHDOG LEDGER")
    print("="*30)
    print(f"💰 Available Cash: ${pf['USD']:.2f}")
    print(f"📈 Total Earnings: ${pf['total_earnings_usd']:.2f}")
    print("-" * 30)

    print("[1] BUY (Add New Lot)")
    print("[2] SELL (Close Specific Lot)")
    print("[3] STATUS (Detailed Holdings)")
    print("[4] EXIT")
    choice = input("\nSelect Option: ")

    # --- 🟢 OPTION 1: LOG A NEW BUY ---
    if choice == "1":
        coin = input("Enter Coin Symbol (e.g., BTCUSDT): ").upper()
        amount = float(input(f"Amount of {coin} bought: "))
        price = float(input(f"Price per {coin}: "))
        cost = amount * price

        if cost > pf["USD"]:
            print(f"❌ Error: Insufficient balance. Cost: ${cost:.2f} | Wallet: ${pf['USD']:.2f}")
            return

        if coin not in pf["positions"] or not isinstance(pf["positions"][coin], list):
            pf["positions"][coin] = []
        
        new_lot = {
            "amount": amount,
            "price": price,
            "usd_value": cost,
            "timestamp": int(datetime.now().timestamp())
        }
        pf["positions"][coin].append(new_lot)
        pf["USD"] -= cost
        save_portfolio(pf)
        print(f"✅ Successfully logged Lot #{len(pf['positions'][coin])} for {coin}.")

    # --- 🔴 OPTION 2: LOG A SELL ---
    elif choice == "2":
        active_coins = [c for c, lots in pf["positions"].items() if len(lots) > 0]
        if not active_coins:
            print("No active positions to sell.")
            return

        for idx, symbol in enumerate(active_coins):
            print(f"[{idx}] {symbol}")

        coin_idx = int(input("\nSelect Coin Index: "))
        symbol = active_coins[coin_idx]
        lots = pf["positions"][symbol]

        for i, lot in enumerate(lots):
            print(f"  [{i}] Lot #{i+1}: {lot['amount']} @ ${lot['price']:,.2f}")

        lot_idx = int(input("\nSelect Lot Index to CLOSE: "))
        sell_price = float(input(f"Actual Selling Price for {symbol}: "))
        
        lot = lots.pop(lot_idx)
        revenue = sell_price * lot['amount']
        profit = revenue - (lot['price'] * lot['amount'])

        pf["USD"] += revenue
        pf["total_earnings_usd"] += profit
        save_portfolio(pf)
        print(f"✅ Lot Closed. Revenue: ${revenue:.2f} | Profit: ${profit:.2f}")

    # --- 📊 OPTION 3: STATUS BREAKDOWN ---
    elif choice == "3":
        print("\n--- 📋 DETAILED HOLDINGS ---")
        found_holdings = False
        for symbol, lots in pf["positions"].items():
            if lots:
                found_holdings = True
                total_qty = sum(l['amount'] for l in lots)
                total_cost = sum(l['usd_value'] for l in lots)
                avg_price = total_cost / total_qty
                print(f"\n🔹 {symbol}")
                print(f"   Total Qty:  {total_qty:,.8f}")
                print(f"   Avg Price:  ${avg_price:,.4f}")
                print(f"   Total Cost: ${total_cost:,.2f}")
                print(f"   Open Lots:  {len(lots)}")
        
        if not found_holdings:
            print("Your portfolio is currently empty.")
        print("\n" + "="*30)

    elif choice == "4":
        return

if __name__ == "__main__":
    run_logger()