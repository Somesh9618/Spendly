import sys
import os
import sqlite3
import json

# Adjust path to find the database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, DB_PATH

def dump_db():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}. Please run the app or verification script first to initialize it.")
        return
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch Users
    cursor.execute("SELECT id, name, email, created_at FROM users")
    users = [dict(row) for row in cursor.fetchall()]
    
    # Fetch Expenses
    cursor.execute("SELECT id, user_id, amount, category, date, description, created_at FROM expenses")
    expenses = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    data = {
        "users": users,
        "expenses": expenses
    }
    
    # Output to stdout
    print("\n=== USERS ===")
    for u in users:
        print(f"ID: {u['id']} | Name: {u['name']} | Email: {u['email']} | Created At: {u['created_at']}")
        
    print("\n=== EXPENSES ===")
    for e in expenses:
        print(f"ID: {e['id']} | User ID: {e['user_id']} | Amount: ${e['amount']:.2f} | Category: {e['category']} | Date: {e['date']} | Description: {e['description']}")
        
    # Write to a JSON file so the agent/dashboard can read it
    dump_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'db_dump.json')
    with open(dump_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Saved structured data dump to {dump_file}")

if __name__ == '__main__':
    dump_db()
