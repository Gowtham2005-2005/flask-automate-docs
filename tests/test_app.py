import pytest
from flask import Flask
import json
import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app after adding the path
from app import app
from models import db, User, UserCreate

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_index_route(client):
    """Test the root route"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Flask Automate Docs Test App is running' in response.data

def test_get_users_empty(client):
    """Test getting users when database is empty"""
    response = client.get('/users')
    assert response.status_code == 200
    assert response.json == []

def test_create_user(client):
    """Test creating a new user"""
    user_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    response = client.post('/users', 
                          data=json.dumps(user_data),
                          content_type='application/json')
    assert response.status_code == 200
    assert b'User created successfully' in response.data

def test_get_user(client):
    """Test getting a specific user"""
    # First create a user
    user_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    client.post('/users', 
                data=json.dumps(user_data),
                content_type='application/json')
    
    # Then get the user
    response = client.get('/users/1')
    assert response.status_code == 200
    assert response.json['name'] == "Test User"
    assert response.json['email'] == "test@example.com"

def test_get_nonexistent_user(client):
    """Test getting a user that doesn't exist"""
    response = client.get('/users/999')
    assert response.status_code == 404

def test_protected_route(client):
    """Test the protected route"""
    response = client.get('/protected')
    assert response.status_code == 200
    assert b'This is protected content' in response.data

def test_create_user_duplicate_email(client):
    """Test creating a user with duplicate email"""
    user_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    # Create first user
    client.post('/users', 
                data=json.dumps(user_data),
                content_type='application/json')
    
    # Try to create second user with same email
    response = client.post('/users', 
                          data=json.dumps(user_data),
                          content_type='application/json')
    assert response.status_code == 400  # Should fail due to unique constraint

def test_create_user_invalid_data(client):
    """Test creating a user with invalid data"""
    user_data = {
        "name": "",  # Empty name
        "email": "invalid-email"  # Invalid email format
    }
    response = client.post('/users', 
                          data=json.dumps(user_data),
                          content_type='application/json')
    assert response.status_code == 400  # Should fail due to validation 