import json
import pytest
from app.models import Course, Test, Question, Option

def test_create_test_as_professor(client, professor_auth_headers, app):
    """Test creating a test as a professor."""
    # First create a course
    with app.app_context():
        from app.models import User, Course
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        course = Course(
            title='Test Course for Tests',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.commit()
        course_id = course.id
    
    response = client.post('/tests', 
                          data=json.dumps({
                              'title': 'Math Test 1',
                              'description': 'Basic mathematics test',
                              'course_id': course_id
                          }),
                          content_type='application/json',
                          headers=professor_auth_headers)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Test created successfully'
    assert data['test']['title'] == 'Math Test 1'

def test_create_test_as_student_forbidden(client, auth_headers, app):
    """Test that students cannot create tests."""
    with app.app_context():
        from app.models import User, Course
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        course = Course(
            title='Test Course',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.commit()
        course_id = course.id
    
    response = client.post('/tests', 
                          data=json.dumps({
                              'title': 'Unauthorized Test',
                              'description': 'Should not be created',
                              'course_id': course_id
                          }),
                          content_type='application/json',
                          headers=auth_headers)
    
    assert response.status_code == 403

def test_add_question_to_test(client, professor_auth_headers, app):
    """Test adding a question to a test."""
    # Create course and test
    with app.app_context():
        from app.models import User, Course, Test
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        course = Course(
            title='Question Test Course',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.flush()
        
        test = Test(
            title='Question Test',
            description='Test for questions',
            course_id=course.id
        )
        db.session.add(test)
        db.session.commit()
        test_id = test.id
    
    response = client.post(f'/tests/{test_id}/questions', 
                          data=json.dumps({
                              'question_text': 'What is 2 + 2?',
                              'question_type': 'mcq',
                              'options': [
                                  {'option_text': '3', 'is_correct': False},
                                  {'option_text': '4', 'is_correct': True},
                                  {'option_text': '5', 'is_correct': False}
                              ]
                          }),
                          content_type='application/json',
                          headers=professor_auth_headers)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Question added successfully'
    assert data['question']['question_text'] == 'What is 2 + 2?'

def test_submit_test_answers(client, auth_headers, app):
    """Test student submitting test answers."""
    # Create course, test, and enroll student
    with app.app_context():
        from app.models import User, Course, Test, Question, Option, Enrollment
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        student = User.query.filter_by(role='student').first()
        
        course = Course(
            title='Submission Test Course',
            description='Test Description',
            professor_id=professor.id
        )
        db.session.add(course)
        db.session.flush()
        
        # Enroll student
        enrollment = Enrollment(
            course_id=course.id,
            student_id=student.id
        )
        db.session.add(enrollment)
        
        test = Test(
            title='Submission Test',
            description='Test for submissions',
            course_id=course.id
        )
        db.session.add(test)
        db.session.flush()
        
        question = Question(
            question_text='What is 2 + 2?',
            question_type='mcq',
            test_id=test.id
        )
        db.session.add(question)
        db.session.flush()
        
        option = Option(
            option_text='4',
            is_correct=True,
            question_id=question.id
        )
        db.session.add(option)
        db.session.commit()
        
        test_id = test.id
        question_id = question.id
        option_id = option.id
    
    response = client.post(f'/tests/{test_id}/submit', 
                          data=json.dumps({
                              'answers': [
                                  {
                                      'question_id': question_id,
                                      'selected_option_id': option_id
                                  }
                              ]
                          }),
                          content_type='application/json',
                          headers=auth_headers)
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Test submitted successfully'

def test_get_test_results_as_professor(client, professor_auth_headers, app):
    """Test professor viewing test results."""
    # Create test with submissions
    with app.app_context():
        from app.models import User, Course, Test, Question, Answer, Enrollment
        from app import db
        
        professor = User.query.filter_by(role='professor').first()
        student = User.query.filter_by(role='student').first()
        
        course = Course(
            title='Results Test Course',
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
        
        test = Test(
            title='Results Test',
            description='Test for results',
            course_id=course.id
        )
        db.session.add(test)
        db.session.flush()
        
        question = Question(
            question_text='Test question?',
            question_type='short_answer',
            test_id=test.id
        )
        db.session.add(question)
        db.session.flush()
        
        answer = Answer(
            student_id=student.id,
            question_id=question.id,
            answer_text='Test answer'
        )
        db.session.add(answer)
        db.session.commit()
        
        test_id = test.id
    
    response = client.get(f'/tests/{test_id}/results', headers=professor_auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'test' in data
    assert 'results' in data
    assert len(data['results']) == 1
