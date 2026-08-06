# pyrefly: ignore [missing-import]
import pytest
from app import app
from database.db import get_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_add_expense_redirects_unauthenticated(client):
    """Verify that visiting /expenses/add without login redirects to /login."""
    response = client.get('/expenses/add')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login' or response.headers['Location'].endswith('/login')

def test_add_expense_authenticated_loads(client):
    """Verify that visiting /expenses/add while logged in returns HTTP 200 and renders form."""
    # Log in first
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/expenses/add')
    assert response.status_code == 200
    assert b"Log an Expense" in response.data
    assert b"Amount" in response.data
    assert b"Category" in response.data
    assert b"Date" in response.data
    assert b"Description (optional)" in response.data

def test_add_expense_valid_submission(client):
    """Verify that submitting valid data inserts it into database and redirects to profile."""
    # Log in first
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    # Pre-check database count
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expenses")
    before_count = cursor.fetchone()[0]
    conn.close()

    # Submit valid data
    response = client.post('/expenses/add', data={
        'amount': '55.50',
        'category': 'Food',
        'date': '2026-08-06',
        'description': 'Tacos lunch'
    })
    
    assert response.status_code == 302
    assert response.headers['Location'] == '/profile' or response.headers['Location'].endswith('/profile')

    # Post-check database count and correctness
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expenses")
    after_count = cursor.fetchone()[0]
    assert after_count == before_count + 1

    cursor.execute("SELECT amount, category, date, description FROM expenses ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    assert row['amount'] == 55.50
    assert row['category'] == 'Food'
    assert row['date'] == '2026-08-06'
    assert row['description'] == 'Tacos lunch'

    # Clean up inserted expense to prevent test database pollution
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE description = 'Tacos lunch'")
    conn.commit()
    conn.close()

def test_add_expense_validation_errors(client):
    """Verify that invalid inputs display appropriate errors and preserve input values."""
    # Log in first
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    # 1. Negative amount
    response = client.post('/expenses/add', data={
        'amount': '-10.00',
        'category': 'Food',
        'date': '2026-08-06',
        'description': 'Invalid negative amount'
    })
    assert response.status_code == 200
    assert b"Amount must be greater than 0." in response.data
    assert b'value="-10.00"' in response.data
    assert b'value="2026-08-06"' in response.data
    assert b'value="Invalid negative amount"' in response.data

    # 2. Invalid category
    response = client.post('/expenses/add', data={
        'amount': '25.00',
        'category': 'InvalidCategoryName',
        'date': '2026-08-06',
        'description': 'Bad category'
    })
    assert response.status_code == 200
    assert b"Invalid category." in response.data
    assert b'value="25.00"' in response.data
    assert b'value="Bad category"' in response.data

    # 3. Invalid date
    response = client.post('/expenses/add', data={
        'amount': '25.00',
        'category': 'Food',
        'date': '2026-08-35', # invalid day
        'description': 'Bad date'
    })
    assert response.status_code == 200
    assert b"Invalid date format." in response.data
    assert b'value="25.00"' in response.data
    assert b'value="2026-08-35"' in response.data
    assert b'value="Bad date"' in response.data

    # 4. Too long description
    long_desc = "x" * 201
    response = client.post('/expenses/add', data={
        'amount': '25.00',
        'category': 'Food',
        'date': '2026-08-06',
        'description': long_desc
    })
    assert response.status_code == 200
    assert b"Description must be 200 characters or less." in response.data
    assert b'value="25.00"' in response.data
    assert long_desc.encode() in response.data
