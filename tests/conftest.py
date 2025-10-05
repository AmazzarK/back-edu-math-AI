import pytest
import json
from app import create_app, db
from app.models import User
from app.utils.auth import hash_password

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        user = User(
            full_name="Test Admin",
            email="admin@test.com",
            password_hash=hash_password("testpass"),
            role="admin"
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def professor_user(app):
    """Create a professor user for testing."""
    with app.app_context():
        user = User(
            full_name="Test Professor",
            email="prof@test.com",
            password_hash=hash_password("testpass"),
            role="professor"
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def student_user(app):
    """Create a student user for testing."""
    with app.app_context():
        user = User(
            full_name="Test Student",
            email="student@test.com",
            password_hash=hash_password("testpass"),
            role="student"
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def auth_headers(client, student_user):
    """Get auth headers for a student user."""
    response = client.post('/auth/login', 
                          data=json.dumps({
                              'email': 'student@test.com',
                              'password': 'testpass'
                          }),
                          content_type='application/json')
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def professor_auth_headers(client, professor_user):
    """Get auth headers for a professor user."""
    response = client.post('/auth/login', 
                          data=json.dumps({
                              'email': 'prof@test.com',
                              'password': 'testpass'
                          }),
                          content_type='application/json')
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get auth headers for an admin user."""
    response = client.post('/auth/login', 
                          data=json.dumps({
                              'email': 'admin@test.com',
                              'password': 'testpass'
                          }),
                          content_type='application/json')
    token = response.get_json()['token']
    return {'Authorization': f'Bearer {token}'}
