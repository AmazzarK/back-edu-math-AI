# Educational Mathematics AI Platform - Backend

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![Redis](https://img.shields.io/badge/Redis-7+-red.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

*A comprehensive Flask-based backend system designed to revolutionize mathematics education through artificial intelligence integration.*

[Features](#features) • [Quick Start](#quick-start) • [API Documentation](#api-documentation) • [Architecture](#architecture) • [Deployment](#deployment)

</div>

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Authentication & Security](#authentication--security)
- [AI Integration](#ai-integration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Educational Mathematics AI Platform is a production-ready Flask backend system that serves as the backbone for an interactive learning management system. It supports multiple user roles (Students, Professors, Administrators) and provides AI-powered educational assistance through OpenAI integration.

### Target Users

- **Students**: Complete exercises, receive AI tutoring, track learning progress
- **Professors**: Create educational content, manage classes, monitor student performance
- **Administrators**: Oversee system operations, manage users, access analytics

### Key Capabilities

- **AI-Powered Tutoring**: OpenAI GPT integration for personalized mathematics assistance
- **Comprehensive Analytics**: Real-time progress tracking and performance insights
- **Multi-Storage Support**: Local filesystem and AWS S3 integration
- **Background Processing**: Celery-powered email notifications and analytics
- **Production Ready**: Docker containerization with comprehensive security measures

## Features

### AI-Powered Education
- **Intelligent Tutoring**: OpenAI GPT-3.5/GPT-4 integration for personalized math assistance
- **Contextual Help**: AI responses tailored to current exercises and learning objectives
- **Conversation Management**: Persistent chat history with educational context
- **Adaptive Learning**: AI-driven difficulty adjustment based on performance

### Multi-Role User Management
- **Role-Based Access Control**: Student, Professor, and Administrator roles
- **Secure Authentication**: JWT tokens with refresh mechanism and blacklisting
- **Profile Management**: Comprehensive user profiles with preferences
- **Email Verification**: Account activation and password reset functionality

### Educational Content Management
- **Exercise Creation**: Flexible exercise types (multiple choice, calculation, essay)
- **Class Management**: Course creation, student enrollment, assignment distribution
- **Progress Tracking**: Real-time performance monitoring and analytics
- **File Upload System**: Secure file storage with local and AWS S3 support

### Advanced Analytics
- **Student Dashboard**: Personalized progress overview and recommendations
- **Professor Insights**: Class performance analytics and student monitoring
- **Admin Analytics**: System-wide statistics and user engagement metrics
- **Real-time Metrics**: Live performance tracking and reporting

### Enterprise Security
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-Based Authorization**: Granular permission system
- **Input Validation**: Comprehensive data validation with Marshmallow
- **Security Headers**: CORS, CSP, and other security configurations

### Performance & Scalability
- **Background Tasks**: Celery integration for email and analytics processing
- **Caching Strategy**: Redis-based caching for optimal performance
- **Database Optimization**: PostgreSQL with proper indexing and relationships
- **Docker Support**: Complete containerization for easy deployment

## Technology Stack

### Core Framework
- **Flask 2.3.3**: Web framework with RESTful API support
- **Flask-RESTful**: REST API development with resource-based routing
- **Flask-JWT-Extended**: JWT authentication and authorization
- **SQLAlchemy 2.0**: Modern ORM with relationship management

### Database & Caching
- **PostgreSQL 15+**: Primary relational database with JSONB support
- **Redis 7**: Caching, session management, and task queue backend
- **Flask-Migrate**: Database migration management

### AI & External Services
- **OpenAI API**: GPT-3.5/GPT-4 integration for educational assistance
- **Celery 5.3**: Asynchronous task processing
- **AWS S3**: Cloud file storage (optional)
- **SMTP**: Email notification delivery

### Development & Deployment
- **Docker & Docker Compose**: Containerization and orchestration
- **Gunicorn**: WSGI server for production deployment
- **pytest**: Comprehensive testing framework
- **Marshmallow**: Data validation and serialization

## Quick Start

### Prerequisites
- **Python 3.11+**
- **PostgreSQL 15+**
- **Redis 7+**
- **Docker** (optional, for containerized deployment)

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/AmazzarK/back-edu-math-AI.git
cd back-edu-math-AI

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=your-super-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/edumath_ai

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=true

# AWS S3 Configuration (Optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### 3. Database Setup

```bash
# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Seed with sample data
python db_manager.py seed
```

### 4. Start the Application

#### Option A: Direct Python
```bash
python run.py
```

#### Option B: Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d
```

The server will be available at `http://localhost:5000`

### 5. Verify Installation

```bash
# Health check
curl http://localhost:5000/health

# Test authentication
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@eduplatform.com", "password": "admin123"}'
```

## Architecture

The platform follows a modern microservices-inspired architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Mobile App    │    │  Third-party    │
│  (React/Vue)    │    │   (Flutter)     │    │  Integrations   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Flask API Gateway     │
                    │   (Authentication & CORS)  │
                    └─────────────┬─────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───┴────┐              ┌────────┴────────┐              ┌────┴────┐
│ Auth   │              │   Business      │              │  File   │
│Service │              │    Logic        │              │ Storage │
└───┬────┘              │   Services      │              └────┬────┘
    │                   └────────┬────────┘                   │
┌───┴────┐                       │                       ┌────┴────┐
│  JWT   │              ┌────────┴────────┐              │AWS S3 / │
│ Token  │              │   Database      │              │ Local   │
│Manager │              │  (PostgreSQL)   │              │ Files   │
└────────┘              └────────┬────────┘              └─────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Background Tasks      │
                    │    (Celery + Redis)       │
                    └───────────────────────────┘
```

### Key Components

#### API Layer (`/app/api/`)
- **RESTful Endpoints**: Resource-based API design with Flask-RESTful
- **Authentication**: JWT-based security with role-based access control
- **Validation**: Marshmallow schemas for input validation and serialization

#### Service Layer (`/app/services/`)
- **Business Logic**: Centralized business rules and operations
- **AI Integration**: OpenAI API communication and response processing
- **File Management**: Multi-storage backend with validation and processing

#### Data Layer (`/app/models.py`)
- **ORM Models**: SQLAlchemy models with relationships and constraints
- **Database Design**: Normalized schema with JSONB for flexible content
- **Migration Management**: Flask-Migrate for version control

#### Background Processing (`/app/tasks/`)
- **Email Notifications**: Asynchronous email delivery with templates
- **Analytics Processing**: Data aggregation and report generation
- **Scheduled Tasks**: Periodic maintenance and cleanup operations

## API Documentation

### Test Accounts

| Role      | Email                     | Password      | Capabilities |
|-----------|---------------------------|---------------|--------------|
| Admin     | admin@eduplatform.com     | admin123      | Full system access, user management, analytics |
| Professor | professor@eduplatform.com | professor123  | Course creation, student monitoring, content management |
| Student   | student@eduplatform.com   | student123    | Exercise completion, AI tutoring, progress tracking |

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/auth/register` | Create new user account | No |
| `POST` | `/api/auth/login` | Authenticate user credentials | No |
| `GET` | `/api/auth/profile` | Get current user profile | Yes |
| `PUT` | `/api/auth/profile` | Update user profile | Yes |
| `POST` | `/api/auth/refresh` | Refresh JWT access token | Yes |
| `POST` | `/api/auth/logout` | Invalidate user session | Yes |

### Exercise Management

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/exercises` | List exercises with filtering | Student+ |
| `POST` | `/api/exercises` | Create new exercise | Professor+ |
| `GET` | `/api/exercises/<id>` | Get exercise details | Student+ |
| `PUT` | `/api/exercises/<id>` | Update exercise | Creator/Admin |
| `DELETE` | `/api/exercises/<id>` | Delete exercise | Creator/Admin |
| `POST` | `/api/exercises/<id>/submit` | Submit exercise answers | Student |

### Class & Course Management

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/classes` | List user's classes | Student+ |
| `POST` | `/api/classes` | Create new class | Professor+ |
| `GET` | `/api/classes/<id>` | Get class details | Enrolled/Professor |
| `POST` | `/api/classes/<id>/enroll` | Enroll in class | Student |
| `PUT` | `/api/classes/<id>` | Update class settings | Professor+ |

### AI Chat Integration

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/chat/message` | Send message to AI tutor | Student+ |
| `GET` | `/api/chat/conversations` | Get conversation history | Student+ |
| `GET` | `/api/chat/conversation/<id>` | Get specific conversation | Owner |
| `DELETE` | `/api/chat/conversation/<id>` | Delete conversation | Owner |

### Analytics & Progress

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/dashboard/student` | Student dashboard data | Student |
| `GET` | `/api/dashboard/professor` | Professor dashboard data | Professor |
| `GET` | `/api/dashboard/admin` | Admin dashboard data | Admin |
| `GET` | `/api/progress/student/<id>` | Student progress details | Self/Professor |
| `GET` | `/api/progress/exercise/<id>` | Exercise analytics | Professor+ |

### File Management

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/files/upload` | Upload file to system | Student+ |
| `GET` | `/api/files` | List user's files | Student+ |
| `GET` | `/api/files/<id>` | Get file metadata | Owner/Authorized |
| `GET` | `/api/files/<id>/download` | Download file content | Owner/Authorized |
| `DELETE` | `/api/files/<id>` | Delete file | Owner/Admin |

### Notification System

| Method | Endpoint | Description | Role Required |
|--------|----------|-------------|---------------|
| `GET` | `/api/notifications` | Get user notifications | Student+ |
| `POST` | `/api/notifications/send` | Send notifications | Professor+ |
| `PUT` | `/api/notifications/<id>/read` | Mark as read | Recipient |

### Example API Usage

#### User Registration
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }'
```

#### User Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@eduplatform.com",
    "password": "Student123!"
  }'
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "user-uuid",
    "email": "student@eduplatform.com",
    "role": "student",
    "profile": {...}
  }
}
```

#### Create Exercise (Professor)
```bash
curl -X POST http://localhost:5000/api/exercises \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Linear Equations Practice",
    "description": "Solve basic linear equations",
    "subject": "Algebra",
    "difficulty": "easy",
    "questions": [
      {
        "type": "multiple_choice",
        "question": "Solve: 2x + 3 = 7",
        "options": ["x = 1", "x = 2", "x = 3", "x = 4"],
        "correct_answer": 1
      }
    ],
    "max_score": 10
  }'
```

#### AI Chat Message
```bash
curl -X POST http://localhost:5000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "message": "Can you help me understand how to solve quadratic equations?",
    "context": {
      "current_exercise": "exercise-id",
      "difficulty_level": "intermediate"
    }
  }'
```

## Database Schema

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('student', 'professor', 'admin')),
    profile_data JSONB,
    is_active BOOLEAN DEFAULT true,
    email_confirmed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Exercises
```sql
CREATE TABLE exercises (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    subject VARCHAR(100),
    difficulty VARCHAR(50) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    questions JSONB NOT NULL,
    solutions JSONB,
    max_score INTEGER,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Progress Tracking
```sql
CREATE TABLE progress (
    id SERIAL PRIMARY KEY,
    student_id UUID REFERENCES users(id),
    exercise_id INTEGER REFERENCES exercises(id),
    status VARCHAR(50) CHECK (status IN ('not_started', 'in_progress', 'completed')),
    score INTEGER,
    answers JSONB,
    time_spent INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### Relationships
- **Users ↔ Classes**: Many-to-many through enrollments
- **Users ↔ Exercises**: One-to-many (professor creates exercises)
- **Students ↔ Progress**: One-to-many (student attempts)
- **Users ↔ Chat Conversations**: One-to-many (user conversations)

## Authentication & Security

### JWT Token Management
- **Access Tokens**: 15-minute expiration for API access
- **Refresh Tokens**: 30-day expiration for token renewal
- **Token Blacklisting**: Immediate invalidation on logout
- **Secure Headers**: Authorization: Bearer `<token>`

### Role-Based Access Control
```python
@role_required('professor', 'admin')
def create_exercise():
    """Only professors and admins can create exercises"""
    pass

@role_required('student')
def submit_answer():
    """Only students can submit answers"""
    pass
```

### Security Features
- **Password Hashing**: bcrypt with salt rounds
- **Input Validation**: Marshmallow schema validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **CORS Configuration**: Controlled cross-origin access
- **Rate Limiting**: API endpoint protection
- **Security Headers**: CSP, HSTS, X-Frame-Options

## AI Integration

### OpenAI Configuration
```python
# AI prompt engineering for educational responses
SYSTEM_PROMPT = """
You are an AI mathematics tutor. Provide step-by-step explanations,
ask guiding questions, and encourage learning through discovery.
Never give direct answers - guide students to solutions.
"""
```

### Conversation Management
- **Context Preservation**: Maintains conversation history
- **Educational Focus**: Responses tailored to learning objectives
- **Adaptive Difficulty**: Adjusts based on student progress
- **Cost Optimization**: Intelligent model selection (GPT-3.5/GPT-4)

### Response Enhancement
- **Mathematical Notation**: LaTeX rendering support
- **Interactive Elements**: Step-by-step breakdowns
- **Related Exercises**: Automatic problem suggestions
- **Progress Integration**: Connected to student learning path

## Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-flask pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Test Structure
```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_auth.py            # Authentication endpoint tests
├── test_exercises.py       # Exercise management tests
├── test_classes.py         # Class management tests
├── test_chat.py           # AI chat integration tests
├── test_files.py          # File upload/download tests
└── test_analytics.py     # Analytics and dashboard tests
```

### Sample Test
```python
def test_user_registration(client):
    """Test user registration endpoint"""
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
        'role': 'student'
    })
    
    assert response.status_code == 201
    assert 'access_token' in response.json
    assert response.json['user']['email'] == 'test@example.com'
```

## Deployment

### Docker Deployment (Recommended)

#### Development Environment
```bash
# Clone and navigate to project
git clone https://github.com/AmazzarK/back-edu-math-AI.git
cd back-edu-math-AI

# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f web
```

#### Production Environment
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale celery=3

# Health check
curl http://localhost:5000/health
```

### Cloud Deployment

#### Render.com
1. **Connect Repository**: Link your GitHub repository to Render
2. **Environment Variables**: Set in Render dashboard
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn --bind 0.0.0.0:$PORT run:app`

#### Railway.app
1. **Connect Repository**: Import from GitHub
2. **Auto-Detection**: Railway detects Flask automatically
3. **Environment Variables**: Configure in dashboard
4. **Automatic Deployment**: Deploys on git push

#### AWS/Digital Ocean
```bash
# Deploy with Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.prod.yml edumath

# Or use Kubernetes
kubectl apply -f k8s/
```

### Environment Variables

#### Required Configuration
```env
# Flask
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_USE_TLS=true
```

#### Optional Configuration
```env
# AWS S3 (for file storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1

# Performance
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Health Monitoring
```bash
# Application health
curl http://localhost:5000/health

# Database connection
curl http://localhost:5000/health/db

# Redis connection
curl http://localhost:5000/health/redis

# Background tasks
curl http://localhost:5000/health/celery
```

## Development

### Project Structure
```
edu-math-ai-back/
├── app/
│   ├── __init__.py           # Flask application factory
│   ├── models.py             # SQLAlchemy models
│   ├── routes/              # API endpoints
│   │   ├── auth.py
│   │   ├── courses.py
│   │   ├── tests.py
│   │   ├── exercises.py
│   │   ├── badges.py
│   │   ├── admin.py
│   │   ├── professor.py
│   │   ├── chatbot.py
│   │   └── health.py
│   └── utils/
│       ├── auth.py          # JWT & auth utilities
│       └── validation.py    # Marshmallow schemas
├── tests/                    # Test suite
├── migrations/               # Database migrations
├── docker-compose.yml        # Development containers
├── docker-compose.prod.yml   # Production containers
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
└── run.py                   # Application entry point
```

### Contributing Guidelines

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests**: Ensure new features have test coverage
4. **Follow coding standards**: Use Black formatter and flake8 linter
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**: Describe your changes clearly

### Code Quality Standards
```bash
# Format code with Black
black app/

# Lint with flake8
flake8 app/

# Type checking with mypy
mypy app/

# Security scanning
bandit -r app/
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U username -d dbname

# Reset migrations (development only)
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

#### JWT Token Issues
```bash
# Verify token format
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5000/api/auth/profile

# Check token expiration
python -c "import jwt; print(jwt.decode('YOUR_TOKEN', verify=False))"
```

#### Redis Connection Problems
```bash
# Test Redis connection
redis-cli ping

# Check Redis logs
sudo journalctl -u redis

# Restart Redis
sudo systemctl restart redis
```

#### OpenAI API Issues
```bash
# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.openai.com/v1/models

# Check rate limits and usage
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.openai.com/v1/usage
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_exercises_subject ON exercises(subject);
CREATE INDEX idx_progress_student_id ON progress(student_id);
```

#### Caching Strategy
```python
# Cache expensive queries
@cache.memoize(timeout=300)
def get_student_analytics(student_id):
    # Expensive analytics computation
    pass
```

#### Background Task Monitoring
```bash
# Monitor Celery workers
celery -A celery_app.celery inspect active

# Worker statistics
celery -A celery_app.celery inspect stats
```

## API Reference

For comprehensive API documentation, visit:
- **Local Development**: `http://localhost:5000/docs`
- **Swagger UI**: Interactive API explorer with request/response examples
- **Postman Collection**: Available in `docs/postman/` directory

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- **Bug Fixes**: Help us squash bugs
- **New Features**: Add educational enhancements
- **Documentation**: Improve docs and examples
- **Testing**: Increase test coverage
- **UI/UX**: Frontend integration improvements
- **Performance**: Optimization opportunities

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **OpenAI**: For providing the GPT models that power our AI tutoring
- **Flask Community**: For the excellent web framework and extensions
- **PostgreSQL Team**: For the robust database system
- **Redis Team**: For the high-performance caching solution
- **Contributors**: Everyone who has contributed to this project

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/AmazzarK/back-edu-math-AI/issues)
- **Documentation**: [Technical documentation](documentation.txt)
- **Email**: contact@edumath-ai.com

---

<div align="center">

**Made with care for mathematics education**

[Star this repository](https://github.com/AmazzarK/back-edu-math-AI) if you find it helpful!

</div>