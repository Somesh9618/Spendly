import pytest
from app import app
from database.db import get_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_budget_requires_login(client):
    """Verify that visiting /budget redirects to /login."""
    response = client.get('/budget')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login' or response.headers['Location'].endswith('/login')

def test_set_and_update_budget(client):
    """Verify that an authenticated user can set and then update a budget."""
    # Login
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    # 1. Set budget
    response = client.post('/budget', data={
        'month': '2026-08',
        'amount': '12500.50'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Check it redirected to profile and displays the budget
    assert b"12,500.50" in response.data
    
    # Verify in DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM budgets WHERE year = 2026 AND month = 8")
    row = cursor.fetchone()
    assert row is not None
    assert row['amount'] == 12500.50
    
    # 2. Update budget
    response = client.post('/budget', data={
        'month': '2026-08',
        'amount': '8000.00'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"8,000.00" in response.data
    
    # Verify update in DB
    cursor.execute("SELECT amount FROM budgets WHERE year = 2026 AND month = 8")
    row = cursor.fetchone()
    assert row['amount'] == 8000.00
    conn.close()

def test_clear_budget(client):
    """Verify that a user can clear/delete an existing budget."""
    # Login
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    # Set a budget first
    client.post('/budget', data={
        'month': '2026-08',
        'amount': '5000.00'
    })
    
    # Clear the budget
    response = client.post('/budget', data={
        'month': '2026-08',
        'amount': '5000.00',
        'clear': 'true'
    }, follow_redirects=True)
    
    # Verify it redirected to profile and shows "No budget configured"
    assert b"No budget configured for this month" in response.data
    
    # Verify in DB it is deleted
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM budgets WHERE year = 2026 AND month = 8")
    row = cursor.fetchone()
    assert row is None
    conn.close()

def test_invalid_budget_validation(client):
    """Verify that invalid inputs (negative/empty amount) return validation errors."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    # Negative budget
    response = client.post('/budget', data={
        'month': '2026-08',
        'amount': '-10.00'
    })
    assert response.status_code == 200
    assert b"Amount must be greater than 0" in response.data
    
    # Empty amount when not clearing
    response = client.post('/budget', data={
        'month': '2026-08',
        'amount': ''
    })
    assert response.status_code == 200
    assert b"Amount must be greater than 0" in response.data
