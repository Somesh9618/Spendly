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

def test_edit_expense_redirects_unauthenticated(client):
    """Verify that visiting /expenses/1/edit without login redirects to /login."""
    response = client.get('/expenses/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login' or response.headers['Location'].endswith('/login')

def test_edit_expense_unauthorized_access(client):
    """Verify that users receive a 404 error if they attempt to edit an expense belonging to another user."""
    # Register and log in a new user
    client.post('/register', data={
        'name': 'New User',
        'email': 'new@spendly.com',
        'password': 'newuser123'
    }, follow_redirects=True)
    client.post('/login', data={'email': 'new@spendly.com', 'password': 'newuser123'})

    # Try to edit expense with ID 1 (which belongs to demo@spendly.com)
    response = client.get('/expenses/1/edit')
    assert response.status_code == 404

def test_edit_expense_loads_form(client):
    """Verify GET /expenses/1/edit renders pre-populated values for the owner."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/expenses/1/edit')
    assert response.status_code == 200
    assert b"Edit Expense" in response.data
    assert b'value="25.50"' in response.data
    assert b"Food" in response.data
    assert b'value="2026-08-01"' in response.data
    assert b'value="Dinner at local diner"' in response.data

def test_edit_expense_valid_update(client):
    """Verify that updating with valid data updates DB and redirects to profile."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})

    # Update expense ID 1
    response = client.post('/expenses/1/edit', data={
        'amount': '30.00',
        'category': 'Food',
        'date': '2026-08-01',
        'description': 'Updated Dinner at local diner'
    })
    assert response.status_code == 302
    assert response.headers['Location'] == '/profile' or response.headers['Location'].endswith('/profile')

    # Verify database update
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT amount, description FROM expenses WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    assert row['amount'] == 30.00
    assert row['description'] == 'Updated Dinner at local diner'

    # Clean up (restore original values) to prevent DB pollution
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE expenses
        SET amount = 25.50, description = 'Dinner at local diner'
        WHERE id = 1
    """)
    conn.commit()
    conn.close()

def test_edit_expense_validation_errors(client):
    """Verify validation failures show proper error messages and preserve input values."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})

    # 1. Negative amount
    response = client.post('/expenses/1/edit', data={
        'amount': '-10.00',
        'category': 'Food',
        'date': '2026-08-01',
        'description': 'Dinner at local diner'
    })
    assert response.status_code == 200
    assert b"Amount must be greater than 0." in response.data
    assert b'value="-10.00"' in response.data

    # 2. Invalid category
    response = client.post('/expenses/1/edit', data={
        'amount': '25.50',
        'category': 'InvalidCategory',
        'date': '2026-08-01',
        'description': 'Dinner at local diner'
    })
    assert response.status_code == 200
    assert b"Invalid category." in response.data

    # 3. Invalid date
    response = client.post('/expenses/1/edit', data={
        'amount': '25.50',
        'category': 'Food',
        'date': 'invalid-date-format',
        'description': 'Dinner at local diner'
    })
    assert response.status_code == 200
    assert b"Invalid date format." in response.data
    assert b'value="invalid-date-format"' in response.data

    # 4. Description too long
    long_desc = "x" * 201
    response = client.post('/expenses/1/edit', data={
        'amount': '25.50',
        'category': 'Food',
        'date': '2026-08-01',
        'description': long_desc
    })
    assert response.status_code == 200
    assert b"Description must be 200 characters or less." in response.data
    assert long_desc.encode() in response.data
