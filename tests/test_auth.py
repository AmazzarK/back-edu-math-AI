import json
import pytest
from app.models import User

def test_user_registration(client):
    """Test user registration."""
    response = client.post('/auth/register', 
                          data=json.dumps({
                              'full_name': 'New User',
                              'email': 'newuser@test.com',
                              'password': 'password123',
                              'role': 'student'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'User created successfully'
    assert data['user']['email'] == 'newuser@test.com'
    assert data['user']['role'] == 'student'

def test_user_registration_duplicate_email(client, student_user):
    """Test registration with duplicate email."""
    response = client.post('/auth/register', 
                          data=json.dumps({
                              'full_name': 'Another User',
                              'email': 'student@test.com',  # Same as existing user
                              'password': 'password123',
                              'role': 'student'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'already exists' in data['error']

def test_user_login_success(client, student_user):
    """Test successful login."""
    response = client.post('/auth/login', 
                          data=json.dumps({
                              'email': 'student@test.com',
                              'password': 'testpass'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Login successful'
    assert 'token' in data
    assert data['user']['email'] == 'student@test.com'

def test_user_login_invalid_credentials(client, student_user):
    """Test login with invalid credentials."""
    response = client.post('/auth/login', 
                          data=json.dumps({
                              'email': 'student@test.com',
                              'password': 'wrongpassword'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 401
    data = response.get_json()
    assert data['error'] == 'Invalid credentials'

def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get('/auth/me', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['email'] == 'student@test.com'
    assert data['role'] == 'student'

def test_get_current_user_no_token(client):
    """Test getting current user without token."""
    response = client.get('/auth/me')
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'Token is missing' in data['error']

def test_registration_validation(client):
    """Test registration with invalid data."""
    # Missing required fields
    response = client.post('/auth/register', 
                          data=json.dumps({
                              'email': 'test@test.com'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'Validation failed' in data['error']
    
    # Invalid email
    response = client.post('/auth/register', 
                          data=json.dumps({
                              'full_name': 'Test User',
                              'email': 'invalid-email',
                              'password': 'password123',
                              'role': 'student'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 400
    
    # Invalid role
    response = client.post('/auth/register', 
                          data=json.dumps({
                              'full_name': 'Test User',
                              'email': 'test@test.com',
                              'password': 'password123',
                              'role': 'invalid_role'
                          }),
                          content_type='application/json')
    
    assert response.status_code == 400
