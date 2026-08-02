# pyrefly: ignore [missing-import]
import pytest
from app import app

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
    """Verify that visiting /profile while logged in returns HTTP 200 and loads correct static content."""
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
    
    # 2. User info card displays correct name and email
    assert b"demo@spendly.com" in response.data
    assert b"Member since" in response.data
    assert b"August 2, 2026" in response.data
    
    # 3. Stats display is present
    assert b"18,240" in response.data
    assert b"34" in response.data
    assert b"Food" in response.data
    
    # 4. Recent transactions are present
    assert b"Dinner at local diner" in response.data
    assert b"Monthly internet subscription" in response.data
    assert b"New running sneakers" in response.data
    
    # 5. Category breakdown details are present
    assert b"Bills" in response.data
    assert b"Shopping" in response.data
