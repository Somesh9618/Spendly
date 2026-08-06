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

def test_delete_expense_redirects_unauthenticated(client):
    """Verify that visiting /expenses/1/delete without login redirects to /login."""
    response = client.get('/expenses/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login' or response.headers['Location'].endswith('/login')

def test_delete_expense_unauthorized_access(client):
    """Verify that users receive a 404 error if they attempt to delete an expense belonging to another user."""
    # Register and log in a new user
    client.post('/register', data={
        'name': 'New User',
        'email': 'new@spendly.com',
        'password': 'newuser123'
    }, follow_redirects=True)
    client.post('/login', data={'email': 'new@spendly.com', 'password': 'newuser123'})

    # Try to delete expense with ID 1 (which belongs to demo@spendly.com)
    response = client.get('/expenses/1/delete')
    assert response.status_code == 404

def test_delete_expense_valid(client):
    """Verify that deleting a valid expense removes it from database and redirects to profile."""
    # 1. Register and log in a user
    client.post('/register', data={
        'name': 'Delete Test User',
        'email': 'deletetest@spendly.com',
        'password': 'testpassword123'
    }, follow_redirects=True)
    client.post('/login', data={'email': 'deletetest@spendly.com', 'password': 'testpassword123'})

    # 2. Add an expense
    client.post('/expenses/add', data={
        'amount': '45.00',
        'category': 'Entertainment',
        'date': '2026-08-06',
        'description': 'Temporary movie ticket'
    })

    # Retrieve the inserted expense's ID from the DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM expenses WHERE description = 'Temporary movie ticket'")
    row = cursor.fetchone()
    expense_id = row['id']
    conn.close()

    # Pre-check db presence
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (expense_id,))
    count_before = cursor.fetchone()[0]
    conn.close()
    assert count_before == 1

    # 3. Call delete route
    response = client.get(f'/expenses/{expense_id}/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/profile' or response.headers['Location'].endswith('/profile')

    # Post-check db presence
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expenses WHERE id = ?", (expense_id,))
    count_after = cursor.fetchone()[0]
    conn.close()
    assert count_after == 0
