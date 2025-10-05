from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import User, Course, Enrollment, Intervention, Test, Answer, Question
from app.utils.auth import token_required, role_required
from app.utils.validation import InterventionSchema
from app import db

professor_bp = Blueprint('professor', __name__)

@professor_bp.route('/students', methods=['GET'])
@token_required
@role_required('professor')
def get_professor_students(current_user):
    """
    Get Students in Professor's Courses
    ---
    tags:
      - Professor
    security:
      - Bearer: []
    responses:
      200:
        description: List of students enrolled in professor's courses
    """
    # Get all courses taught by this professor
    courses = Course.query.filter_by(professor_id=current_user.id).all()
    course_ids = [course.id for course in courses]
    
    # Get all enrollments for these courses
    enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).all()
    
    # Get unique students
    student_ids = list(set([enrollment.student_id for enrollment in enrollments]))
    students = User.query.filter(User.id.in_(student_ids)).all()
    
    students_data = []
    for student in students:
        student_dict = student.to_dict()
        # Add enrollment info
        student_courses = []
        for enrollment in enrollments:
            if enrollment.student_id == student.id:
                course = next(c for c in courses if c.id == enrollment.course_id)
                student_courses.append({
                    'course_id': course.id,
                    'course_title': course.title,
                    'enrolled_at': enrollment.enrolled_at.isoformat()
                })
        student_dict['enrolled_courses'] = student_courses
        students_data.append(student_dict)
    
    return jsonify(students_data), 200

@professor_bp.route('/students/<student_id>', methods=['GET'])
@token_required
@role_required('professor')
def get_student_detail(current_user, student_id):
    """
    Get Student Detail and Progress
    ---
    tags:
      - Professor
    security:
      - Bearer: []
    parameters:
      - in: path
        name: student_id
        type: string
        required: true
    responses:
      200:
        description: Student details with progress
      404:
        description: Student not found
      403:
        description: Student not in professor's courses
    """
    student = User.query.filter_by(id=student_id, role='student').first()
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    
    # Check if student is enrolled in any of professor's courses
    professor_courses = Course.query.filter_by(professor_id=current_user.id).all()
    professor_course_ids = [course.id for course in professor_courses]
    
    student_enrollments = Enrollment.query.filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id.in_(professor_course_ids)
    ).all()
    
    if not student_enrollments:
        return jsonify({'error': 'Student not enrolled in your courses'}), 403
    
    # Get student's test performance
    test_performance = []
    for course in professor_courses:
        course_tests = Test.query.filter_by(course_id=course.id).all()
        for test in course_tests:
            # Get student's answers for this test
            answers = db.session.query(Answer).join(Question).filter(
                Question.test_id == test.id,
                Answer.student_id == student_id
            ).all()
            
            if answers:
                total_questions = len(test.questions)
                answered_questions = len(answers)
                test_performance.append({
                    'test_id': test.id,
                    'test_title': test.title,
                    'course_title': course.title,
                    'total_questions': total_questions,
                    'answered_questions': answered_questions,
                    'completion_rate': (answered_questions / total_questions * 100) if total_questions > 0 else 0
                })
    
    # Get interventions for this student
    interventions = Intervention.query.filter_by(
        professor_id=current_user.id,
        student_id=student_id
    ).order_by(Intervention.created_at.desc()).all()
    
    return jsonify({
        'student': student.to_dict(),
        'enrolled_courses': [
            {
                'course_id': enrollment.course_id,
                'course_title': next(c.title for c in professor_courses if c.id == enrollment.course_id),
                'enrolled_at': enrollment.enrolled_at.isoformat()
            }
            for enrollment in student_enrollments
        ],
        'test_performance': test_performance,
        'interventions': [intervention.to_dict() for intervention in interventions]
    }), 200

@professor_bp.route('/interventions', methods=['POST'])
@token_required
@role_required('professor')
def add_intervention(current_user):
    """
    Add Intervention Note
    ---
    tags:
      - Professor
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            student_id:
              type: string
            note:
              type: string
    responses:
      201:
        description: Intervention added successfully
      400:
        description: Validation error
      403:
        description: Student not in professor's courses
    """
    try:
        schema = InterventionSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Verify student is in professor's courses
    professor_courses = Course.query.filter_by(professor_id=current_user.id).all()
    professor_course_ids = [course.id for course in professor_courses]
    
    student_enrollment = Enrollment.query.filter(
        Enrollment.student_id == data['student_id'],
        Enrollment.course_id.in_(professor_course_ids)
    ).first()
    
    if not student_enrollment:
        return jsonify({'error': 'Student not enrolled in your courses'}), 403
    
    new_intervention = Intervention(
        professor_id=current_user.id,
        student_id=data['student_id'],
        note=data['note']
    )
    
    db.session.add(new_intervention)
    db.session.commit()
    
    return jsonify({
        'message': 'Intervention added successfully',
        'intervention': new_intervention.to_dict()
    }), 201

@professor_bp.route('/interventions', methods=['GET'])
@token_required
@role_required('professor')
def get_interventions(current_user):
    """
    Get Professor's Interventions
    ---
    tags:
      - Professor
    security:
      - Bearer: []
    responses:
      200:
        description: List of interventions by this professor
    """
    interventions = Intervention.query.filter_by(professor_id=current_user.id).order_by(Intervention.created_at.desc()).all()
    
    return jsonify([intervention.to_dict() for intervention in interventions]), 200

@professor_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required('professor')
def get_professor_dashboard(current_user):
    """
    Get Professor Dashboard Data
    ---
    tags:
      - Professor
    security:
      - Bearer: []
    responses:
      200:
        description: Dashboard statistics and recent activity
    """
    # Get professor's courses
    courses = Course.query.filter_by(professor_id=current_user.id).all()
    course_ids = [course.id for course in courses]
    
    # Get enrollment count
    total_enrollments = Enrollment.query.filter(Enrollment.course_id.in_(course_ids)).count()
    
    # Get unique students count
    unique_students = db.session.query(Enrollment.student_id).filter(
        Enrollment.course_id.in_(course_ids)
    ).distinct().count()
    
    # Get tests count
    total_tests = Test.query.filter(Test.course_id.in_(course_ids)).count()
    
    # Get recent interventions
    recent_interventions = Intervention.query.filter_by(professor_id=current_user.id).order_by(
        Intervention.created_at.desc()
    ).limit(5).all()
    
    return jsonify({
        'total_courses': len(courses),
        'total_students': unique_students,
        'total_enrollments': total_enrollments,
        'total_tests': total_tests,
        'courses': [course.to_dict() for course in courses],
        'recent_interventions': [intervention.to_dict() for intervention in recent_interventions]
    }), 200
