import sys
import os
import random
import datetime
import sqlite3

# Adjust path to find the database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db

def parse_args():
    if len(sys.argv) < 4:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)
    
    try:
        user_id = int(sys.argv[1])
        count = int(sys.argv[2])
        months = int(sys.argv[3])
        return user_id, count, months
    except ValueError:
        print("Usage: /seed-expenses <user_id> <count> <months>")
        print("Example: /seed-expenses 1 50 6")
        sys.exit(1)

def verify_user(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone() is None:
        print(f"No user found with id {user_id}.")
        sys.exit(1)

# Realistic Indian descriptions for each category
DESCRIPTIONS = {
    "Food": [
        "Swiggy order for dinner", "Zomato lunch delivery", "Groceries from Zepto",
        "Masala tea and samosa at local stall", "Dinner at Udipi restaurant",
        "South Indian breakfast at Darshini", "Biryani from Paradise Biryani", "Subway lunch wrap"
    ],
    "Transport": [
        "Ola cab ride to office", "Uber Auto fare", "Metro smart card recharge",
        "Petrol refill at Indian Oil", "Auto rickshaw fare for local travel",
        "Train ticket booking", "Bus pass renewal"
    ],
    "Bills": [
        "Electricity bill payment via Google Pay", "Airtel fiber broadband bill",
        "Jio mobile recharge", "LPG gas cylinder booking", "Maintenance charges for apartment",
        "Water bill payment"
    ],
    "Health": [
        "Medicines from Apollo Pharmacy", "Consultation fees at clinic",
        "Eye checkup and new glasses", "Dental cleaning", "Pathology lab blood tests",
        "Health insurance premium payment"
    ],
    "Entertainment": [
        "BookMyShow movie tickets (PVR)", "Netflix monthly subscription",
        "Spotify Premium renewal", "Bowling at the mall", "Weekend trip ticket",
        "Standup comedy show tickets"
    ],
    "Shopping": [
        "Clothes from Myntra", "Shoes from Ajio", "Electronics purchase on Amazon India",
        "Household items from D-Mart", "Gift for friend's wedding", "Home decor from local market"
    ],
    "Other": [
        "Stationery items", "Dry cleaning charges", "Mobile cover replacement",
        "Home cleaning supplies", "Courier charges", "Temple donation"
    ]
}

# Range details: (min_amt, max_amt)
RANGES = {
    "Food": (50, 800),
    "Transport": (20, 500),
    "Bills": (200, 3000),
    "Health": (100, 2000),
    "Entertainment": (100, 1500),
    "Shopping": (200, 5000),
    "Other": (50, 1000)
}

# Category weights for proportional distribution (Food most common, Health & Ent least)
CATEGORIES = ["Food", "Transport", "Bills", "Shopping", "Other", "Health", "Entertainment"]
WEIGHTS = [0.35, 0.20, 0.15, 0.12, 0.08, 0.05, 0.05]

def generate_expenses(user_id, count, months):
    expenses = []
    today = datetime.date.today()
    days_range = months * 30  # approximate 30 days per month
    
    for _ in range(count):
        # Pick category based on weight
        category = random.choices(CATEGORIES, weights=WEIGHTS, k=1)[0]
        
        # Pick amount within range
        min_amt, max_amt = RANGES[category]
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        # Pick random description
        description = random.choice(DESCRIPTIONS[category])
        
        # Random date in the past
        days_ago = random.randint(0, days_range)
        date = today - datetime.timedelta(days=days_ago)
        date_str = date.strftime("%Y-%m-%d")
        
        expenses.append((user_id, amount, category, date_str, description))
    
    return expenses

def main():
    user_id, count, months = parse_args()
    
    conn = get_db()
    verify_user(conn, user_id)
    
    expenses_data = generate_expenses(user_id, count, months)
    
    # Insert in single transaction
    cursor = conn.cursor()
    try:
        cursor.executemany("""
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (?, ?, ?, ?, ?)
        """, expenses_data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error during insertion: {e}. Transaction rolled back.")
        sys.exit(1)
    finally:
        conn.close()
        
    # Get stats
    dates = [e[3] for e in expenses_data]
    min_date = min(dates)
    max_date = max(dates)
    
    print("Expenses seeded successfully:")
    print(f"- Number of expenses inserted: {count}")
    print(f"- Date range: {min_date} to {max_date}")
    
    print("\nSample of 5 inserted records:")
    sample = random.sample(expenses_data, min(5, count))
    for s in sample:
        print(f"  Category: {s[2]} | Amount: INR {s[1]} | Date: {s[3]} | Description: {s[4]}")

if __name__ == '__main__':
    main()
