import sys
import os
import sqlite3

# Adjust python path to be able to import from root folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db, init_db, seed_db, DB_PATH

def run_tests():
    print("Starting database verification script...")
    
    # 1. Clean up existing database file for a clean verification run
    if os.path.exists(DB_PATH):
        print(f"Removing existing database file {DB_PATH} for clean test run.")
        os.remove(DB_PATH)
        
    # 2. Run initialization and seeding
    print("Running init_db()...")
    init_db()
    
    print("Running seed_db()...")
    seed_db()
    
    # 3. Check file creation
    if not os.path.exists(DB_PATH):
        raise AssertionError("Database file was not created!")
    print("✓ Database file created successfully.")
    
    # 4. Open connection
    conn = get_db()
    cursor = conn.cursor()
    
    # 5. Check tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    assert 'users' in tables, "Table 'users' was not created!"
    assert 'expenses' in tables, "Table 'expenses' was not created!"
    print("✓ Both 'users' and 'expenses' tables exist.")
    
    # 6. Verify seed user
    cursor.execute("SELECT * FROM users WHERE email = 'demo@spendly.com'")
    user = cursor.fetchone()
    assert user is not None, "Demo User not found!"
    assert user['name'] == 'Demo User', f"Expected name 'Demo User', got {user['name']}"
    assert user['password_hash'].startswith('scrypt:') or user['password_hash'].startswith('pbkdf2:'), "Password hash format is invalid!"
    user_id = user['id']
    print(f"✓ Demo User verification passed. User ID is {user_id}.")
    
    # 7. Verify unique email constraint
    try:
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES ('Another User', 'demo@spendly.com', 'some_hash')
        """)
        conn.commit()
        raise AssertionError("Unique email constraint failed: was able to insert duplicate email!")
    except sqlite3.IntegrityError:
        print("✓ Unique email constraint is working.")
        
    # 8. Verify foreign key constraint
    try:
        # User ID 99999 should not exist, so this insert should fail
        cursor.execute("""
            INSERT INTO expenses (user_id, amount, category, date, description)
            VALUES (99999, 10.0, 'Food', '2026-08-01', 'Test fail')
        """)
        conn.commit()
        raise AssertionError("Foreign key constraint failed: was able to insert expense for invalid user_id!")
    except sqlite3.IntegrityError:
        print("✓ Foreign key constraint is working.")
        
    # 9. Verify 8 sample expenses and categories
    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
    expenses = cursor.fetchall()
    assert len(expenses) == 8, f"Expected 8 expenses, got {len(expenses)}"
    print("✓ Exactly 8 sample expenses found.")
    
    categories = set(row['category'] for row in expenses)
    expected_categories = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}
    assert expected_categories.issubset(categories), f"Missing categories! Got: {categories}"
    print("✓ All 7 required categories are represented in the seed data.")
    
    for row in expenses:
        date_str = row['date']
        # Check date format YYYY-MM-DD
        parts = date_str.split('-')
        assert len(parts) == 3 and len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2, \
            f"Date format is invalid: {date_str}"
    print("✓ All expense dates follow the YYYY-MM-DD format.")
    
    # 10. Verify no duplicate seed data on repeated runs
    print("Running seed_db() again to check for idempotency...")
    seed_db()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM expenses")
    expense_count = cursor.fetchone()['count']
    
    assert user_count == 1, f"Duplicate users created! Count is {user_count}"
    assert expense_count == 8, f"Duplicate expenses created! Count is {expense_count}"
    print("✓ Seeding is idempotent (no duplicate data inserted on repeated calls).")
    
    conn.close()
    print("\nAll database tests passed successfully!")

if __name__ == '__main__':
    try:
        run_tests()
    except Exception as e:
        print(f"\nVerification FAILED: {e}", file=sys.stderr)
        sys.exit(1)
