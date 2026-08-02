# pyrefly: ignore [missing-import]
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_login_page_loads(client):
    """Verify that the login page loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Sign in" in response.data

def test_successful_login(client):
    """Verify that valid credentials log the user in, create session, and show authenticated navbar."""
    # Seeded credentials
    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Redirects directly to landing page
    assert b"Track every rupee" in response.data
    assert b"Profile" in response.data
    assert b"Logout" in response.data
    assert b"Sign in" not in response.data

def test_failed_login(client):
    """Verify that invalid credentials yield an error and keep guest navbar state."""
    response = client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    # Guest links are still shown
    assert b"Sign in" in response.data
    assert b"Get started" in response.data
    # Authenticated links are not shown
    assert b"Profile" not in response.data

def test_logout(client):
    """Verify that logout clears user session and redirects to home page."""
    # Log in first
    client.post('/login', data={
        'email': 'demo@spendly.com',
        'password': 'demo123'
    })
    
    # Log out
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    
    # Check that we are back at the landing page
    assert b"Track every rupee" in response.data
    
    # Navbar shows guest options
    assert b"Sign in" in response.data
    assert b"Get started" in response.data
    assert b"Profile" not in response.data
