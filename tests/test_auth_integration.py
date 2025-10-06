"""
Integration tests for authentication flows.
Comprehensive testing of all auth endpoints and scenarios.
"""
import pytest
import json
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User

@pytest.fixture
def app():
    """Create test application."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def sample_user_data():
    """Sample user registration data."""
    return {
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'confirm_password': 'SecurePass123!',
        'role': 'student',
        'first_name': 'John',
        'last_name': 'Doe'
    }

@pytest.fixture
def registered_user(app, sample_user_data):
    """Create a registered user."""
    with app.app_context():
        user = User(
            email=sample_user_data['email'],
            role=sample_user_data['role'],
            profile_data={
                'first_name': sample_user_data['first_name'],
                'last_name': sample_user_data['last_name'],
                'phone': '',
                'bio': '',
                'avatar_url': '',
                'preferences': {
                    'language': 'en',
                    'timezone': 'UTC',
                    'email_notifications': True
                }
            }
        )
        user.set_password(sample_user_data['password'])
        db.session.add(user)
        db.session.commit()
        return user

class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_successful_registration(self, client, sample_user_data):
        """Test successful user registration."""
        response = client.post('/auth/register',
                              data=json.dumps(sample_user_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'User registered successfully'
        assert 'user' in data
        assert data['user']['email'] == sample_user_data['email']
        assert data['user']['role'] == sample_user_data['role']
    
    def test_registration_duplicate_email(self, client, registered_user, sample_user_data):
        """Test registration with duplicate email."""
        response = client.post('/auth/register',
                              data=json.dumps(sample_user_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already exists' in data['message']
    
    def test_registration_password_mismatch(self, client, sample_user_data):
        """Test registration with password mismatch."""
        data = sample_user_data.copy()
        data['confirm_password'] = 'DifferentPassword123!'
        
        response = client.post('/auth/register',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'validation_failed' in response_data['error']
    
    def test_registration_weak_password(self, client, sample_user_data):
        """Test registration with weak password."""
        data = sample_user_data.copy()
        data['password'] = 'weak'
        data['confirm_password'] = 'weak'
        
        response = client.post('/auth/register',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'validation_failed' in response_data['error']
    
    def test_registration_invalid_email(self, client, sample_user_data):
        """Test registration with invalid email."""
        data = sample_user_data.copy()
        data['email'] = 'invalid-email'
        
        response = client.post('/auth/register',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'validation_failed' in response_data['error']
    
    def test_registration_invalid_role(self, client, sample_user_data):
        """Test registration with invalid role."""
        data = sample_user_data.copy()
        data['role'] = 'invalid_role'
        
        response = client.post('/auth/register',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 400
        response_data = response.get_json()
        assert 'validation_failed' in response_data['error']

class TestUserLogin:
    """Test user login functionality."""
    
    def test_successful_login(self, client, registered_user):
        """Test successful login."""
        login_data = {
            'email': registered_user.email,
            'password': 'SecurePass123!'
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Login successful'
        assert 'access_token' in data
        assert 'refresh_token' in data
        assert 'user' in data
        assert data['user']['email'] == registered_user.email
    
    def test_login_invalid_email(self, client):
        """Test login with invalid email."""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'SecurePass123!'
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'authentication_failed' in data['error']
    
    def test_login_invalid_password(self, client, registered_user):
        """Test login with invalid password."""
        login_data = {
            'email': registered_user.email,
            'password': 'WrongPassword123!'
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'authentication_failed' in data['error']
    
    def test_login_inactive_user(self, client, registered_user):
        """Test login with inactive user."""
        # Deactivate user
        registered_user.is_active = False
        db.session.commit()
        
        login_data = {
            'email': registered_user.email,
            'password': 'SecurePass123!'
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'deactivated' in data['message']

class TestUserProfile:
    """Test user profile functionality."""
    
    def get_auth_headers(self, client, user_email, password='SecurePass123!'):
        """Helper to get authentication headers."""
        login_data = {
            'email': user_email,
            'password': password
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        token = response.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def test_get_profile(self, client, registered_user):
        """Test getting user profile."""
        headers = self.get_auth_headers(client, registered_user.email)
        
        response = client.get('/auth/profile', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['email'] == registered_user.email
        assert data['role'] == registered_user.role
        assert 'profile_data' in data
    
    def test_update_profile(self, client, registered_user):
        """Test updating user profile."""
        headers = self.get_auth_headers(client, registered_user.email)
        
        update_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'bio': 'Updated bio',
            'phone': '+1234567890'
        }
        
        response = client.put('/auth/profile',
                             data=json.dumps(update_data),
                             content_type='application/json',
                             headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Profile updated successfully'
        assert data['user']['profile_data']['first_name'] == 'Jane'
        assert data['user']['profile_data']['last_name'] == 'Smith'
    
    def test_profile_without_token(self, client):
        """Test accessing profile without token."""
        response = client.get('/auth/profile')
        
        assert response.status_code == 401

class TestTokenRefresh:
    """Test token refresh functionality."""
    
    def test_token_refresh(self, client, registered_user):
        """Test token refresh."""
        # Login to get tokens
        login_data = {
            'email': registered_user.email,
            'password': 'SecurePass123!'
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        tokens = response.get_json()
        refresh_token = tokens['refresh_token']
        
        # Use refresh token
        headers = {'Authorization': f'Bearer {refresh_token}'}
        
        response = client.post('/auth/refresh', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert data['message'] == 'Token refreshed successfully'

class TestPasswordReset:
    """Test password reset functionality."""
    
    def test_forgot_password(self, client, registered_user):
        """Test forgot password request."""
        data = {'email': registered_user.email}
        
        response = client.post('/auth/forgot-password',
                              data=json.dumps(data),
                              content_type='application/json')
        
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'reset link has been sent' in response_data['message']
    
    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with nonexistent email."""
        data = {'email': 'nonexistent@example.com'}
        
        response = client.post('/auth/forgot-password',
                              data=json.dumps(data),
                              content_type='application/json')
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
    
    def test_reset_password_with_valid_token(self, client, registered_user):
        """Test password reset with valid token."""
        # Simulate setting reset token
        reset_token = 'valid_reset_token'
        registered_user.profile_data = registered_user.profile_data or {}
        registered_user.profile_data['reset_token'] = reset_token
        registered_user.profile_data['reset_token_expires'] = (
            datetime.utcnow() + timedelta(hours=1)
        ).isoformat()
        db.session.commit()
        
        reset_data = {
            'token': reset_token,
            'password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }
        
        response = client.post('/auth/reset-password',
                              data=json.dumps(reset_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Password reset successful'
    
    def test_reset_password_with_invalid_token(self, client):
        """Test password reset with invalid token."""
        reset_data = {
            'token': 'invalid_token',
            'password': 'NewSecurePass123!',
            'confirm_password': 'NewSecurePass123!'
        }
        
        response = client.post('/auth/reset-password',
                              data=json.dumps(reset_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid or expired' in data['message']

class TestChangePassword:
    """Test password change functionality."""
    
    def get_auth_headers(self, client, user_email, password='SecurePass123!'):
        """Helper to get authentication headers."""
        login_data = {
            'email': user_email,
            'password': password
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        token = response.get_json()['access_token']
        return {'Authorization': f'Bearer {token}'}
    
    def test_change_password_success(self, client, registered_user):
        """Test successful password change."""
        headers = self.get_auth_headers(client, registered_user.email)
        
        change_data = {
            'current_password': 'SecurePass123!',
            'new_password': 'NewSecurePass456!',
            'confirm_password': 'NewSecurePass456!'
        }
        
        response = client.post('/auth/change-password',
                              data=json.dumps(change_data),
                              content_type='application/json',
                              headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Password changed successfully'
    
    def test_change_password_wrong_current(self, client, registered_user):
        """Test password change with wrong current password."""
        headers = self.get_auth_headers(client, registered_user.email)
        
        change_data = {
            'current_password': 'WrongPassword123!',
            'new_password': 'NewSecurePass456!',
            'confirm_password': 'NewSecurePass456!'
        }
        
        response = client.post('/auth/change-password',
                              data=json.dumps(change_data),
                              content_type='application/json',
                              headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'incorrect' in data['message']

class TestLogout:
    """Test logout functionality."""
    
    def test_logout_success(self, client, registered_user):
        """Test successful logout."""
        # Login first
        login_data = {
            'email': registered_user.email,
            'password': 'SecurePass123!'
        }
        
        response = client.post('/auth/login',
                              data=json.dumps(login_data),
                              content_type='application/json')
        
        token = response.get_json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Logout
        response = client.post('/auth/logout', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['message'] == 'Logout successful'
