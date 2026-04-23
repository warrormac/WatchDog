import json
import os
import yaml

def load_config():
    with open("config/master.yaml", "r") as f:
        return yaml.safe_load(f)

def load_portfolio(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"USD": 100.0, "total_earnings_usd": 0.0, "positions": {}}

def save_portfolio(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def run_logger():
    config = load_config()
    pf_path = config["vault"]["portfolio_path"]
    pf = load_portfolio(pf_path)

    print(f"\n--- 🛡️ WATCHDOG LEDGER ---")
    print(f"Available Cash: ${pf['USD']:.2f}")
    print(f"Total Earnings: ${pf['total_earnings_usd']:.2f}")
    print("-" * 25)

    # 1. SELECT ACTION
    print("\n[1] BUY (Add Position)")
    print("[2] SELL (Close Position)")
    action_choice = input("Select Option (1 or 2): ")
    action = "buy" if action_choice == "1" else "sell"

    # 2. SELECT COIN
    existing_coins = list(pf["positions"].keys())
    print("\nExisting Coins:")
    for i, coin in enumerate(existing_coins):
        amount = pf["positions"][coin]["amount"]
        print(f"[{i+1}] {coin} (Holdings: {amount})")
    
    print(f"[{len(existing_coins) + 1}] NEW COIN (Type manually)")
    
    coin_choice = int(input("Select Coin Number: "))
    
    if coin_choice <= len(existing_coins):
        symbol = existing_coins[coin_choice - 1]
    else:
        symbol = input("Enter New Symbol (e.g., ETHUSDT): ").upper()

    # 3. ENTER TRADE DATA
    amount = float(input(f"Amount of {symbol}: "))
    price = float(input(f"Price per {symbol}: "))
    total_cost = amount * price

    if action == "buy":
        # Calculate Weighted Average Cost Basis
        if symbol not in pf["positions"]:
            pf["positions"][symbol] = {"amount": 0.0, "cost_basis": 0.0, "usd_value": 0.0}
        
        current_data = pf["positions"][symbol]
        total_old_cost = current_data["amount"] * current_data["cost_basis"]
        total_new_cost = amount * price
        
        # New Total Amount
        new_amount = current_data["amount"] + amount
        
        # Weighted Average: (Old Total Cost + New Total Cost) / New Total Amount
        new_basis = (total_old_cost + total_new_cost) / new_amount
        
        pf["USD"] -= total_new_cost
        pf["positions"][symbol]["amount"] = new_amount
        pf["positions"][symbol]["cost_basis"] = new_basis
        pf["positions"][symbol]["usd_value"] = new_amount * new_basis
        
        print(f"✅ LOGGED: Bought {amount} {symbol} at ${price:.4f}. New Average Basis: ${new_basis:.4f}")

    elif action == "sell":
        if symbol not in pf["positions"] or pf["positions"][symbol]["amount"] <= 0:
            print("❌ ERROR: You don't own this coin!")
            return

        current_data = pf["positions"][symbol]
        # We use the cost_basis to calculate profit on the portion sold
        original_investment_value = current_data["cost_basis"] * amount
        trade_profit = (amount * price) - original_investment_value
        
        pf["USD"] += (amount * price)
        pf["total_earnings_usd"] += trade_profit
        
        # Reduce amount
        pf["positions"][symbol]["amount"] -= amount
        
        # CLEANUP: If amount is near zero, reset everything to 0
        if pf["positions"][symbol]["amount"] <= 0.00000001:
            pf["positions"][symbol]["amount"] = 0.0
            pf["positions"][symbol]["cost_basis"] = 0.0
            pf["positions"][symbol]["usd_value"] = 0.0
        else:
            # Update the remaining USD value based on the original basis
            pf["positions"][symbol]["usd_value"] = pf["positions"][symbol]["amount"] * current_data["cost_basis"]
        
        print(f"💰 LOGGED: Sold {amount} {symbol}. Trade Profit: ${trade_profit:.4f}")

    # 5. COMMIT TO VAULT
    save_portfolio(pf_path, pf)
    print("--- Vault Updated Successfully ---\n")

if __name__ == "__main__":
    run_logger()