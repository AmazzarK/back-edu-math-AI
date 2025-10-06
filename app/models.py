import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.extensions import db
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('student', 'professor', 'admin', name='user_roles'), nullable=False, default='student')
    profile_data = db.Column(JSONB, nullable=False, default=lambda: {
        'first_name': '',
        'last_name': '',
        'phone': '',
        'bio': '',
        'avatar_url': '',
        'preferences': {
            'language': 'en',
            'timezone': 'UTC',
            'email_notifications': True
        }
    })
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    courses_taught = db.relationship('Course', backref='professor', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='student', lazy=True, cascade='all, delete-orphan')
    chatbot_messages = db.relationship('ChatbotMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    student_badges = db.relationship('StudentBadge', backref='student', lazy=True, cascade='all, delete-orphan')
    interventions_given = db.relationship('Intervention', foreign_keys='Intervention.professor_id', backref='professor', lazy=True, cascade='all, delete-orphan')
    interventions_received = db.relationship('Intervention', foreign_keys='Intervention.student_id', backref='student_target', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """Initialize user with default profile data."""
        super(User, self).__init__(**kwargs)
        if not self.profile_data:
            self.profile_data = {
                'first_name': '',
                'last_name': '',
                'phone': '',
                'bio': '',
                'avatar_url': '',
                'preferences': {
                    'language': 'en',
                    'timezone': 'UTC',
                    'email_notifications': True
                }
            }
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def full_name(self):
        """Get full name from profile data."""
        first_name = self.profile_data.get('first_name', '')
        last_name = self.profile_data.get('last_name', '')
        return f"{first_name} {last_name}".strip() or self.email.split('@')[0]
    
    def update_profile(self, data):
        """Update profile data."""
        if not self.profile_data:
            self.profile_data = {}
        
        # Update profile fields
        for key, value in data.items():
            if key in ['first_name', 'last_name', 'phone', 'bio', 'avatar_url']:
                self.profile_data[key] = value
            elif key == 'preferences' and isinstance(value, dict):
                if 'preferences' not in self.profile_data:
                    self.profile_data['preferences'] = {}
                self.profile_data['preferences'].update(value)
        
        # Mark as modified for JSONB
        db.session.merge(self)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_sensitive=False):
        """Convert to dictionary."""
        data = {
            'id': str(self.id),
            'email': self.email,
            'role': self.role,
            'profile_data': self.profile_data or {},
            'is_active': self.is_active,
            'email_confirmed': self.email_confirmed,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'full_name': self.full_name
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
        
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    professor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    tests = db.relationship('Test', backref='course', lazy=True, cascade='all, delete-orphan')
    exercises = db.relationship('Exercise', backref='course', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'professor_id': str(self.professor_id),
            'professor_name': self.professor.full_name if self.professor else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'student_id': str(self.student_id),
            'enrolled_at': self.enrolled_at.isoformat()
        }

class Test(db.Model):
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='test', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Enum('mcq', 'short_answer', 'true_false', name='question_types'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    options = db.relationship('Option', backref='question', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'test_id': self.test_id,
            'options': [option.to_dict() for option in self.options],
            'created_at': self.created_at.isoformat()
        }

class Option(db.Model):
    __tablename__ = 'options'
    
    id = db.Column(db.Integer, primary_key=True)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'option_text': self.option_text,
            'is_correct': self.is_correct,
            'question_id': self.question_id
        }

class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)
    answer_text = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    selected_option = db.relationship('Option', backref='answers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': str(self.student_id),
            'question_id': self.question_id,
            'selected_option_id': self.selected_option_id,
            'answer_text': self.answer_text,
            'score': self.score,
            'submitted_at': self.submitted_at.isoformat()
        }

class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.Enum('easy', 'medium', 'hard', name='difficulty_levels'), 
                          nullable=False, default='medium')
    subject = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('multiple_choice', 'short_answer', 'calculation', 'essay', name='exercise_types'), 
                    nullable=False, default='multiple_choice')
    questions = db.Column(JSONB, nullable=False, default=list)  # List of question objects
    solutions = db.Column(JSONB, nullable=False, default=list)  # Corresponding solutions
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)
    max_score = db.Column(db.Float, nullable=False, default=100.0)
    time_limit = db.Column(db.Integer, nullable=True)  # Time limit in minutes
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    tags = db.Column(JSONB, nullable=False, default=list)  # Subject tags for filtering
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_exercises')
    progress_records = db.relationship('Progress', backref='exercise', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_solutions=False):
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'subject': self.subject,
            'type': self.type,
            'questions': self.questions,
            'created_by': str(self.created_by),
            'creator_name': self.creator.full_name if self.creator else None,
            'course_id': self.course_id,
            'max_score': self.max_score,
            'time_limit': self.time_limit,
            'is_published': self.is_published,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_solutions:
            data['solutions'] = self.solutions
            
        return data
    
    def calculate_score(self, student_answers):
        """Calculate score based on student answers and solutions."""
        if not self.solutions or not student_answers:
            return 0.0
        
        total_questions = len(self.solutions)
        correct_answers = 0
        
        for i, solution in enumerate(self.solutions):
            if i < len(student_answers):
                student_answer = student_answers[i]
                
                if self.type == 'multiple_choice':
                    if student_answer.get('selected_option') == solution.get('correct_option'):
                        correct_answers += 1
                elif self.type == 'calculation':
                    # Simple numeric comparison with tolerance
                    try:
                        student_val = float(student_answer.get('answer', 0))
                        correct_val = float(solution.get('answer', 0))
                        tolerance = solution.get('tolerance', 0.01)
                        if abs(student_val - correct_val) <= tolerance:
                            correct_answers += 1
                    except (ValueError, TypeError):
                        pass
                elif self.type == 'short_answer':
                    # Simple string comparison (case insensitive)
                    student_text = str(student_answer.get('answer', '')).strip().lower()
                    correct_text = str(solution.get('answer', '')).strip().lower()
                    if student_text == correct_text:
                        correct_answers += 1
        
        return (correct_answers / total_questions) * self.max_score if total_questions > 0 else 0.0


class Progress(db.Model):
    __tablename__ = 'progress'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    score = db.Column(db.Float, nullable=True)
    status = db.Column(db.Enum('not_started', 'in_progress', 'completed', 'submitted', name='progress_status'), 
                      nullable=False, default='not_started')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    time_spent = db.Column(db.Integer, nullable=True)  # Time in seconds
    answers = db.Column(JSONB, nullable=True, default=list)  # Student's answers
    feedback = db.Column(JSONB, nullable=True, default=dict)  # Automated feedback
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], backref='progress_records')
    
    # Unique constraint to prevent duplicate progress records
    __table_args__ = (db.UniqueConstraint('student_id', 'exercise_id', name='unique_student_exercise'),)
    
    def to_dict(self, include_answers=False):
        data = {
            'id': self.id,
            'student_id': str(self.student_id),
            'exercise_id': self.exercise_id,
            'score': self.score,
            'status': self.status,
            'attempts': self.attempts,
            'time_spent': self.time_spent,
            'feedback': self.feedback,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'student_name': self.student.full_name if self.student else None,
            'exercise_title': self.exercise.title if self.exercise else None
        }
        
        if include_answers:
            data['answers'] = self.answers
            
        return data
    
    def start_attempt(self):
        """Mark progress as started."""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()
            self.attempts += 1
        elif self.status == 'completed':
            # Allow retaking
            self.status = 'in_progress'
            self.attempts += 1
        
        self.updated_at = datetime.utcnow()
    
    def submit_answers(self, answers, auto_score=True):
        """Submit answers and optionally calculate score."""
        self.answers = answers
        self.status = 'submitted'
        self.submitted_at = datetime.utcnow()
        self.completed_at = datetime.utcnow()
        
        if auto_score and self.exercise:
            self.score = self.exercise.calculate_score(answers)
            self.status = 'completed'
        
        self.updated_at = datetime.utcnow()
        return self.score

class ChatbotMessage(db.Model):
    __tablename__ = 'chatbot_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    sender_role = db.Column(db.Enum('student', 'ai', name='sender_roles'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': str(self.user_id),
            'sender_role': self.sender_role,
            'message': self.message,
            'created_at': self.created_at.isoformat()
        }

class Badge(db.Model):
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student_badges = db.relationship('StudentBadge', backref='badge', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon_url': self.icon_url,
            'created_at': self.created_at.isoformat()
        }

class StudentBadge(db.Model):
    __tablename__ = 'student_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': str(self.student_id),
            'badge_id': self.badge_id,
            'badge': self.badge.to_dict() if self.badge else None,
            'earned_at': self.earned_at.isoformat()
        }

class Intervention(db.Model):
    __tablename__ = 'interventions'
    
    id = db.Column(db.Integer, primary_key=True)
    professor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'professor_id': str(self.professor_id),
            'student_id': str(self.student_id),
            'professor_name': self.professor.full_name if self.professor else None,
            'student_name': self.student_target.full_name if self.student_target else None,
            'note': self.note,
            'created_at': self.created_at.isoformat()
        }

class ChatConversation(db.Model):
    """AI Chatbot conversation model."""
    __tablename__ = 'chat_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    messages = db.Column(JSONB, nullable=False, default=list)  # Array of message objects
    context = db.Column(JSONB, nullable=True, default=dict)  # Conversation context
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self, include_messages=True):
        data = {
            'id': self.id,
            'user_id': str(self.user_id),
            'title': self.title,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': len(self.messages) if self.messages else 0
        }
        
        if include_messages:
            data['messages'] = self.messages or []
            data['context'] = self.context or {}
        
        return data
    
    def add_message(self, role, content, metadata=None):
        """Add a message to the conversation."""
        if not self.messages:
            self.messages = []
        
        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata or {}
        }
        
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        
        # Auto-generate title from first user message
        if not self.title and role == 'user' and len(self.messages) <= 2:
            self.title = content[:50] + ('...' if len(content) > 50 else '')


class Class(db.Model):
    """Class/Course management model."""
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    subject = db.Column(db.String(100), nullable=False)
    grade_level = db.Column(db.String(50), nullable=True)
    professor_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    class_code = db.Column(db.String(10), unique=True, nullable=False)  # For easy joining
    max_students = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    settings = db.Column(JSONB, nullable=False, default=dict)  # Class-specific settings
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    enrollments = db.relationship('ClassEnrollment', backref='class_obj', lazy=True, cascade='all, delete-orphan')
    assigned_exercises = db.relationship('ClassExerciseAssignment', backref='class_obj', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_stats=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'subject': self.subject,
            'grade_level': self.grade_level,
            'professor_id': str(self.professor_id),
            'professor_name': self.professor.full_name if self.professor else None,
            'class_code': self.class_code,
            'max_students': self.max_students,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'settings': self.settings or {},
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_stats:
            data['student_count'] = len(self.enrollments)
            data['exercise_count'] = len(self.assigned_exercises)
        
        return data
    
    @staticmethod
    def generate_class_code():
        """Generate a unique class code."""
        import random
        import string
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Class.query.filter_by(class_code=code).first():
                return code


class ClassEnrollment(db.Model):
    """Student enrollment in classes."""
    __tablename__ = 'class_enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    enrollment_status = db.Column(db.Enum('active', 'inactive', 'dropped', name='enrollment_status'), 
                                 default='active', nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('class_id', 'student_id', name='unique_class_student'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'class_id': self.class_id,
            'student_id': str(self.student_id),
            'student_name': self.student.full_name if self.student else None,
            'enrollment_status': self.enrollment_status,
            'enrolled_at': self.enrolled_at.isoformat()
        }


class ClassExerciseAssignment(db.Model):
    """Exercise assignments to classes."""
    __tablename__ = 'class_exercise_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    assigned_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    is_mandatory = db.Column(db.Boolean, default=True, nullable=False)
    points_worth = db.Column(db.Float, nullable=True)
    instructions = db.Column(db.Text, nullable=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    exercise = db.relationship('Exercise', backref='class_assignments')
    assigner = db.relationship('User', foreign_keys=[assigned_by])
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('class_id', 'exercise_id', name='unique_class_exercise'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'class_id': self.class_id,
            'exercise_id': self.exercise_id,
            'exercise_title': self.exercise.title if self.exercise else None,
            'assigned_by': str(self.assigned_by),
            'assigner_name': self.assigner.full_name if self.assigner else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_mandatory': self.is_mandatory,
            'points_worth': self.points_worth,
            'instructions': self.instructions,
            'assigned_at': self.assigned_at.isoformat()
        }


class UploadedFile(db.Model):
    """File upload management."""
    __tablename__ = 'uploaded_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # image, document, video, etc.
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_path = db.Column(db.String(500), nullable=False)  # Local or S3 path
    storage_type = db.Column(db.Enum('local', 's3', name='storage_types'), default='local', nullable=False)
    uploader_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    metadata = db.Column(JSONB, nullable=True, default=dict)  # Additional file metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'storage_type': self.storage_type,
            'uploader_id': str(self.uploader_id),
            'uploader_name': self.uploader.full_name if self.uploader else None,
            'is_public': self.is_public,
            'metadata': self.metadata or {},
            'created_at': self.created_at.isoformat()
        }
    
    @property
    def file_size_human(self):
        """Human readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class Notification(db.Model):
    """User notifications."""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(
        'email_sent', 'exercise_assigned', 'progress_update', 
        'class_enrollment', 'achievement_earned', 'system_alert',
        name='notification_types'
    ), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    data = db.Column(JSONB, nullable=True, default=dict)  # Additional notification data
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref='notifications')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': str(self.user_id),
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'data': self.data or {},
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None
        }
    
    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()
