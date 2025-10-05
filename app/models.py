import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('student', 'professor', 'admin', name='user_roles'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    courses_taught = db.relationship('Course', backref='professor', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='student', lazy=True, cascade='all, delete-orphan')
    chatbot_messages = db.relationship('ChatbotMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    student_badges = db.relationship('StudentBadge', backref='student', lazy=True, cascade='all, delete-orphan')
    interventions_given = db.relationship('Intervention', foreign_keys='Intervention.professor_id', backref='professor', lazy=True, cascade='all, delete-orphan')
    interventions_received = db.relationship('Intervention', foreign_keys='Intervention.student_id', backref='student_target', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

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
    content = db.Column(JSONB)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'content': self.content,
            'course_id': self.course_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

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
