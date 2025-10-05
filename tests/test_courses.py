import json
import pytest
from app.models import Course, Enrollment

def test_create_course_as_professor(client, professor_auth_headers):
    """Test creating a course as a professor."""
    response = client.post('/courses', 
                          data=json.dumps({
                              'title': 'Test Course',
                              'description': 'A test course'
                          }),
                          content_type='application/json',
                          headers=professor_auth_headers)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Course created successfully'
    assert data['course']['title'] == 'Test Course'

def test_create_course_as_student_forbidden(client, auth_headers):
    """Test that students cannot create courses."""
    response = client.post('/courses', 
                          data=json.dumps({
                              'title': 'Test Course',
                              'description': 'A test course'
                          }),
                          content_type='application/json',
                          headers=auth_headers)
    
    assert response.status_code == 403

def test_get_courses_as_student(client, auth_headers, app):
    """Test getting courses as a student (only enrolled courses)."""
    # First create a course and enroll the student
    with app.app_context():
        from app.models import User, Course, Enrollment
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        student = User.query.filter_by(role='student').first()
        
        course = Course(
            title='Test Course',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.flush()
        
        enrollment = Enrollment(
            course_id=course.id,
            student_id=student.id
        )
        db.session.add(enrollment)
        db.session.commit()
    
    response = client.get('/courses', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Test Course'

def test_enroll_in_course(client, auth_headers, app):
    """Test student enrolling in a course."""
    # First create a course
    with app.app_context():
        from app.models import User, Course
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        course = Course(
            title='Enrollment Test Course',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.commit()
        course_id = course.id
    
    response = client.post(f'/courses/{course_id}/enroll', headers=auth_headers)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Enrolled successfully'

def test_enroll_in_course_already_enrolled(client, auth_headers, app):
    """Test enrolling in a course when already enrolled."""
    # First create a course and enroll the student
    with app.app_context():
        from app.models import User, Course, Enrollment
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        student = User.query.filter_by(role='student').first()
        
        course = Course(
            title='Double Enrollment Test',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.flush()
        
        enrollment = Enrollment(
            course_id=course.id,
            student_id=student.id
        )
        db.session.add(enrollment)
        db.session.commit()
        course_id = course.id
    
    # Try to enroll again
    response = client.post(f'/courses/{course_id}/enroll', headers=auth_headers)
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'Already enrolled' in data['error']

def test_course_validation(client, professor_auth_headers):
    """Test course creation with invalid data."""
    # Missing title
    response = client.post('/courses', 
                          data=json.dumps({
                              'description': 'A test course'
                          }),
                          content_type='application/json',
                          headers=professor_auth_headers)
    
    assert response.status_code == 400
    
    # Title too short
    response = client.post('/courses', 
                          data=json.dumps({
                              'title': 'A',
                              'description': 'A test course'
                          }),
                          content_type='application/json',
                          headers=professor_auth_headers)
    
    assert response.status_code == 400
