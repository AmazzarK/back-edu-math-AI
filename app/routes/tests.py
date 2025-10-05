from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from app.models import Test, Question, Option, Answer, Course, Enrollment
from app.utils.auth import token_required, role_required
from app.utils.validation import TestSchema, QuestionSchema, AnswerSchema
from app import db

tests_bp = Blueprint('tests', __name__)

@tests_bp.route('', methods=['GET'])
@token_required
def get_tests(current_user):
    """
    Get Tests
    ---
    tags:
      - Tests
    security:
      - Bearer: []
    responses:
      200:
        description: List of tests
    """
    if current_user.role == 'student':
        # Students see tests from enrolled courses
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        course_ids = [enrollment.course_id for enrollment in enrollments]
        tests = Test.query.filter(Test.course_id.in_(course_ids)).all()
    elif current_user.role == 'professor':
        # Professors see tests from their courses
        courses = Course.query.filter_by(professor_id=current_user.id).all()
        course_ids = [course.id for course in courses]
        tests = Test.query.filter(Test.course_id.in_(course_ids)).all()
    else:
        # Admins see all tests
        tests = Test.query.all()
    
    return jsonify([test.to_dict() for test in tests]), 200

@tests_bp.route('/<int:test_id>', methods=['GET'])
@token_required
def get_test(current_user, test_id):
    """
    Get Single Test
    ---
    tags:
      - Tests
    security:
      - Bearer: []
    parameters:
      - in: path
        name: test_id
        type: integer
        required: true
    responses:
      200:
        description: Test details with questions
      404:
        description: Test not found
    """
    test = Test.query.get_or_404(test_id)
    
    # Check permissions
    if current_user.role == 'student':
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=test.course_id
        ).first()
        if not enrollment:
            return jsonify({'error': 'Not enrolled in this course'}), 403
    elif current_user.role == 'professor':
        if test.course.professor_id != current_user.id:
            return jsonify({'error': 'Not authorized to view this test'}), 403
    
    test_dict = test.to_dict()
    test_dict['questions'] = [question.to_dict() for question in test.questions]
    
    return jsonify(test_dict), 200

@tests_bp.route('', methods=['POST'])
@token_required
@role_required('professor', 'admin')
def create_test(current_user):
    """
    Create New Test
    ---
    tags:
      - Tests
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            course_id:
              type: integer
    responses:
      201:
        description: Test created successfully
      400:
        description: Validation error
      403:
        description: Not authorized
    """
    try:
        schema = TestSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    # Check if professor owns the course
    course = Course.query.get_or_404(data['course_id'])
    if current_user.role == 'professor' and course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to create test for this course'}), 403
    
    new_test = Test(
        title=data['title'],
        description=data.get('description', ''),
        course_id=data['course_id']
    )
    
    db.session.add(new_test)
    db.session.commit()
    
    return jsonify({
        'message': 'Test created successfully',
        'test': new_test.to_dict()
    }), 201

@tests_bp.route('/<int:test_id>/questions', methods=['POST'])
@token_required
@role_required('professor', 'admin')
def add_question(current_user, test_id):
    """
    Add Question to Test
    ---
    tags:
      - Tests
    security:
      - Bearer: []
    parameters:
      - in: path
        name: test_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            question_text:
              type: string
            question_type:
              type: string
              enum: [mcq, short_answer, true_false]
            options:
              type: array
              items:
                type: object
                properties:
                  option_text:
                    type: string
                  is_correct:
                    type: boolean
    responses:
      201:
        description: Question added successfully
      400:
        description: Validation error
    """
    test = Test.query.get_or_404(test_id)
    
    # Check if professor owns the course
    if current_user.role == 'professor' and test.course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to add questions to this test'}), 403
    
    try:
        schema = QuestionSchema()
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
    
    new_question = Question(
        question_text=data['question_text'],
        question_type=data['question_type'],
        test_id=test_id
    )
    
    db.session.add(new_question)
    db.session.flush()  # Get the question ID
    
    # Add options if provided (for MCQ questions)
    if data.get('options'):
        for option_data in data['options']:
            option = Option(
                option_text=option_data['option_text'],
                is_correct=option_data.get('is_correct', False),
                question_id=new_question.id
            )
            db.session.add(option)
    
    db.session.commit()
    
    return jsonify({
        'message': 'Question added successfully',
        'question': new_question.to_dict()
    }), 201

@tests_bp.route('/<int:test_id>/submit', methods=['POST'])
@token_required
@role_required('student')
def submit_test(current_user, test_id):
    """
    Submit Test Answers
    ---
    tags:
      - Tests
    security:
      - Bearer: []
    parameters:
      - in: path
        name: test_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            answers:
              type: array
              items:
                type: object
                properties:
                  question_id:
                    type: integer
                  selected_option_id:
                    type: integer
                  answer_text:
                    type: string
    responses:
      201:
        description: Test submitted successfully
      400:
        description: Validation error
      403:
        description: Not enrolled in course
    """
    test = Test.query.get_or_404(test_id)
    
    # Check enrollment
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=test.course_id
    ).first()
    if not enrollment:
        return jsonify({'error': 'Not enrolled in this course'}), 403
    
    answers_data = request.json.get('answers', [])
    
    for answer_data in answers_data:
        try:
            schema = AnswerSchema()
            validated_answer = schema.load(answer_data)
        except ValidationError as err:
            return jsonify({'error': 'Validation failed', 'messages': err.messages}), 400
        
        # Check if answer already exists (prevent duplicate submissions)
        existing_answer = Answer.query.filter_by(
            student_id=current_user.id,
            question_id=validated_answer['question_id']
        ).first()
        
        if existing_answer:
            # Update existing answer
            existing_answer.selected_option_id = validated_answer.get('selected_option_id')
            existing_answer.answer_text = validated_answer.get('answer_text')
        else:
            # Create new answer
            new_answer = Answer(
                student_id=current_user.id,
                question_id=validated_answer['question_id'],
                selected_option_id=validated_answer.get('selected_option_id'),
                answer_text=validated_answer.get('answer_text')
            )
            db.session.add(new_answer)
    
    db.session.commit()
    
    return jsonify({'message': 'Test submitted successfully'}), 201

@tests_bp.route('/<int:test_id>/results', methods=['GET'])
@token_required
@role_required('professor', 'admin')
def get_test_results(current_user, test_id):
    """
    Get Test Results
    ---
    tags:
      - Tests
    security:
      - Bearer: []
    parameters:
      - in: path
        name: test_id
        type: integer
        required: true
    responses:
      200:
        description: Test results with student submissions
      403:
        description: Not authorized
    """
    test = Test.query.get_or_404(test_id)
    
    # Check if professor owns the course
    if current_user.role == 'professor' and test.course.professor_id != current_user.id:
        return jsonify({'error': 'Not authorized to view results for this test'}), 403
    
    # Get all answers for this test
    answers = db.session.query(Answer).join(Question).filter(
        Question.test_id == test_id
    ).all()
    
    # Group answers by student
    student_results = {}
    for answer in answers:
        student_id = str(answer.student_id)
        if student_id not in student_results:
            student_results[student_id] = {
                'student': answer.student.to_dict(),
                'answers': []
            }
        student_results[student_id]['answers'].append(answer.to_dict())
    
    return jsonify({
        'test': test.to_dict(),
        'results': list(student_results.values())
    }), 200
