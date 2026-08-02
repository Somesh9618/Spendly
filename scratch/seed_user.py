import sys
import os
import random
# pyrefly: ignore [missing-import]
from werkzeug.security import generate_password_hash

# Adjust path to find the database module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import get_db

# Lists of realistic Indian first names and last names across regions
FIRST_NAMES = [
    "Rahul", "Amit", "Rohan", "Priya", "Anjali", "Vikram", "Sanjay", 
    "Sneha", "Rajesh", "Kavita", "Neha", "Arjun", "Divya", "Manish", 
    "Sunita", "Deepak", "Aarav", "Ishaan", "Sai", "Lakshmi"
]

LAST_NAMES = [
    "Sharma", "Patel", "Verma", "Kumar", "Gupta", "Mehta", "Singh", 
    "Joshi", "Reddy", "Rao", "Nair", "Das", "Sen", "Chawla", "Iyer", 
    "Deshmukh", "Choudhury", "Bose", "Pillai", "Menon"
]

def generate_random_user(conn):
    cursor = conn.cursor()
    
    while True:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        
        # Email format: rahul.sharma91@gmail.com (with 2-3 digit number suffix)
        suffix = random.randint(10, 999)
        email = f"{first.lower()}.{last.lower()}{suffix}@gmail.com"
        
        # Verify uniqueness of email
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is None:
            return name, email

def seed_user():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Generate unique user details
    name, email = generate_random_user(conn)
    
    # 2. Hash password "password123"
    password_hash = generate_password_hash("password123")
    
    # 3. Insert into the database
    cursor.execute("""
        INSERT INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
    """, (name, email, password_hash))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 4. Print confirmation details
    print("User seeded successfully:")
    print(f"ID: {user_id}")
    print(f"Name: {name}")
    print(f"Email: {email}")

if __name__ == '__main__':
    seed_user()
