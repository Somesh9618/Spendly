import pytest
from app import app
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_profile_redirects_unauthenticated(client):
    """Verify that visiting /profile without login redirects to /login."""
    response = client.get('/profile')
    assert response.status_code == 302
    assert response.headers['Location'] == '/login' or response.headers['Location'].endswith('/login')

def test_profile_authenticated_loads(client):
    """Verify that visiting /profile while logged in returns HTTP 200 and loads correct live database content."""
    # Log in first using the seeded user
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    
    response = client.get('/profile')
    assert response.status_code == 200
    
    # 1. Nav bar shows dynamic logged-in state
    assert b"Hello," in response.data
    assert b"Demo User" in response.data
    assert b"Logout" in response.data
    
    # 2. User info card displays correct name, email, and join date
    assert b"demo@spendly.com" in response.data
    assert b"Member since" in response.data
    
    from database.db import get_db
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT created_at FROM users WHERE email = 'demo@spendly.com'")
    row = cursor.fetchone()
    conn.close()
    
    dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
    expected_join_date = dt.strftime("%B %d, %Y").replace(" 0", " ")
    assert expected_join_date.encode() in response.data
    
    # 3. Stats display is present and matches seeded database calculations
    assert b"361.74" in response.data
    assert b"8" in response.data
    assert b"Bills" in response.data
    
    # 4. Recent transactions are present (max 5 sorted by date/id descending)
    assert b"Afternoon coffee and pastry" in response.data
    assert b"Workspace notebook" in response.data
    assert b"New running sneakers" in response.data
    assert b"Cinema tickets with friends" in response.data
    assert b"Vitamins and prescription refill" in response.data
    
    # "Daily commute subway fare" (the 2nd expense) should NOT be in the top 5
    assert b"Daily commute subway fare" not in response.data
    
    # 5. Category breakdown details are present
    assert b"Bills" in response.data
    assert b"Shopping" in response.data
    assert b"Food" in response.data

def test_profile_empty_state(client):
    """Verify that a user with no expenses sees correct empty states and fallback messages."""
    # Register and log in a new user
    client.post('/register', data={
        'name': 'New User',
        'email': 'new@spendly.com',
        'password': 'newuser123'
    }, follow_redirects=True)
    
    client.post('/login', data={
        'email': 'new@spendly.com',
        'password': 'newuser123'
    }, follow_redirects=True)
    
    response = client.get('/profile')
    assert response.status_code == 200
    
    # Check that stats are defaulted
    assert b"0.00" in response.data
    assert b"0" in response.data
    assert b"N/A" in response.data
    
    # Check that friendly fallbacks are displayed
    assert b"No recent transactions" in response.data
    assert b"No spending recorded yet" in response.data

def test_profile_date_filter_valid_range(client):
    """Verify that filtering by a valid date range displays only matching expenses and aggregates."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/profile?start_date=2026-08-01&end_date=2026-08-02')
    assert response.status_code == 200
    
    # Total spent: 25.50 (Food) + 15.00 (Transport) + 120.00 (Bills) + 45.00 (Health) = 205.50
    # Count: 4
    # Top Category: Bills
    assert b"205.50" in response.data
    assert b"4" in response.data
    assert b"Bills" in response.data
    
    # Transactions in range must show
    assert b"Dinner at local diner" in response.data
    assert b"Monthly internet subscription" in response.data
    
    # Transactions outside range must NOT show
    assert b"Cinema tickets with friends" not in response.data

def test_profile_date_filter_single_start(client):
    """Verify that providing only start_date filters expenses from that date forward."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/profile?start_date=2026-08-04')
    assert response.status_code == 200
    
    # Seeded expenses:
    # 2026-08-04: Workspace notebook (12.50)
    # 2026-08-05: Afternoon coffee and pastry (18.75)
    # Total: 31.25
    # Count: 2
    assert b"31.25" in response.data
    assert b"2" in response.data
    assert b"Workspace notebook" in response.data
    assert b"Afternoon coffee and pastry" in response.data
    assert b"Cinema tickets with friends" not in response.data

def test_profile_date_filter_single_end(client):
    """Verify that providing only end_date filters expenses up to that date."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/profile?end_date=2026-08-02')
    assert response.status_code == 200
    
    # Total: 205.50, Count: 4
    assert b"205.50" in response.data
    assert b"4" in response.data
    assert b"Dinner at local diner" in response.data
    assert b"Cinema tickets with friends" not in response.data

def test_profile_date_filter_invalid_range(client):
    """Verify that start_date > end_date returns an error and empty states."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/profile?start_date=2026-08-05&end_date=2026-08-01')
    assert response.status_code == 200
    
    assert b"Start date cannot be after end date." in response.data
    assert b"0.00" in response.data
    assert b"0" in response.data
    assert b"N/A" in response.data
    assert b"No recent transactions" in response.data
    assert b"No spending recorded yet" in response.data

def test_profile_date_filter_ui_persistence_and_clear(client):
    """Verify that inputs retain value and a clear/reset link is present."""
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'})
    
    response = client.get('/profile?start_date=2026-08-01&end_date=2026-08-03')
    assert response.status_code == 200
    
    assert b'value="2026-08-01"' in response.data
    assert b'value="2026-08-03"' in response.data
    
    # Verify the clear link exists (href pointing to /profile without params)
    assert b'href="/profile"' in response.data
