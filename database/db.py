import os
import sqlite3
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash

# Path to the database file in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'spendly.db')

def get_db():
    """Opens a connection to the SQLite database and configures row factory and foreign keys."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates the users and expenses tables if they do not exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Create expenses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def seed_db():
    """Seeds the database with a demo user and initial sample expenses if not already seeded."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if the users table already contains data
    cursor.execute("SELECT id FROM users LIMIT 1")
    if cursor.fetchone() is not None:
        conn.close()
        return
        
    # Insert Demo User
    demo_password_hash = generate_password_hash("demo123")
    cursor.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, ("Demo User", "demo@spendly.com", demo_password_hash))
    
    # Get the generated user ID for the demo user
    user_id = cursor.lastrowid
    
    # Define 8 sample expenses spread across the current month of August 2026,
    # ensuring at least one expense per category from the fixed list:
    # Food, Transport, Bills, Health, Entertainment, Shopping, Other
    sample_expenses = [
        (user_id, 25.50, "Food", "2026-08-01", "Dinner at local diner"),
        (user_id, 15.00, "Transport", "2026-08-01", "Daily commute subway fare"),
        (user_id, 120.00, "Bills", "2026-08-02", "Monthly internet subscription"),
        (user_id, 45.00, "Health", "2026-08-02", "Vitamins and prescription refill"),
        (user_id, 35.00, "Entertainment", "2026-08-03", "Cinema tickets with friends"),
        (user_id, 89.99, "Shopping", "2026-08-03", "New running sneakers"),
        (user_id, 12.50, "Other", "2026-08-04", "Workspace notebook"),
        (user_id, 18.75, "Food", "2026-08-05", "Afternoon coffee and pastry")
    ]
    
    cursor.executemany("""
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
    """, sample_expenses)
    
    conn.commit()
    conn.close()
