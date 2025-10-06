# Educational Mathematics AI Platform - Backend

A production-ready Flask backend for an educational platform supporting Students, Professors, and Administrators with comprehensive authentication, role-based access control, and user management.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Database
```bash
python seed.py
```

### 3. Start the Server
```bash
python start.py
```

The server will start on `http://localhost:5000`

## 🧪 Test Accounts

| Role      | Email                     | Password      |
|-----------|---------------------------|---------------|
| Admin     | admin@eduplatform.com     | admin123      |
| Professor | professor@eduplatform.com | professor123  |
| Student   | student@eduplatform.com   | student123    |

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - User Registration
- `POST /api/auth/login` - User Login
- `GET /api/auth/profile` - Get User Profile (Protected)
- `PUT /api/auth/profile` - Update User Profile (Protected)
- `POST /api/auth/refresh` - Refresh JWT Token
- `POST /api/auth/logout` - Logout User (Protected)
- `POST /api/auth/forgot-password` - Request Password Reset
- `POST /api/auth/reset-password` - Reset Password

## 🔧 Postman Testing

### 1. User Registration
```http
POST http://localhost:5000/api/auth/register
Content-Type: application/json

{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
}
```

### 2. User Login
```http
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "email": "student@eduplatform.com",
    "password": "student123"
}
```

**Response includes:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {...}
}
```

### 3. Get Profile (Protected)
```http
GET http://localhost:5000/api/auth/profile
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 4. Update Profile (Protected)
```http
PUT http://localhost:5000/api/auth/profile
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "first_name": "Jane",
    "last_name": "Smith",
    "profile_data": {
        "bio": "Mathematics enthusiast",
        "preferences": {
            "language": "en",
            "notifications": true
        }
    }
}
```

### 5. Password Reset Request
```http
POST http://localhost:5000/api/auth/forgot-password
Content-Type: application/json

{
    "email": "student@eduplatform.com"
}
```

### 6. Token Refresh
```http
POST http://localhost:5000/api/auth/refresh
Authorization: Bearer YOUR_REFRESH_TOKEN
```

## 🏗 Architecture Overview

```
app/
├── __init__.py           # App factory
├── models.py            # Database models
├── api/
│   └── auth.py          # Authentication endpoints
├── schemas/
│   └── auth.py          # Marshmallow validation schemas
├── services/
│   ├── auth.py          # Authentication business logic
│   └── email.py         # Email service (stub)
├── utils/
│   └── auth.py          # RBAC decorators
└── extensions/
    └── __init__.py      # Flask extensions
```

## 🔒 Security Features

- **JWT Authentication** with access and refresh tokens
- **Password Hashing** using bcrypt
- **Role-Based Access Control** (Student, Professor, Admin)
- **Rate Limiting** on authentication endpoints
- **Input Validation** with Marshmallow schemas
- **CORS Protection** for cross-origin requests

### 3. Database Setup

```bash
# Initialize database
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade

# Seed database with sample data
python seed.py
```

### 4. Run the Application

```bash
# Development server
python run.py

# Or using Flask CLI
flask run
```

The API will be available at `http://localhost:5000`

## 📚 API Documentation

Visit `http://localhost:5000/api/docs` for interactive Swagger documentation.

## 🔐 Default Users (After Seeding)

| Role      | Email                      | Password   |
|-----------|----------------------------|------------|
| Admin     | admin@eduplatform.com      | admin123   |
| Professor | professor@eduplatform.com  | prof123    |
| Student   | student@eduplatform.com    | student123 |

## 🧱 Database Models

### Core Models
- **User**: Students, Professors, Admins with role-based access
- **Course**: Professor-created courses
- **Enrollment**: Student-course relationships
- **Test**: Course assessments with questions
- **Question**: MCQ, short answer, true/false questions
- **Option**: Multiple choice options
- **Answer**: Student test submissions
- **Exercise**: Interactive learning content
- **Badge**: Achievement system
- **StudentBadge**: Earned achievements
- **Intervention**: Professor notes on students
- **ChatbotMessage**: AI chat conversations

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Current user info

### Courses
- `GET /courses` - List courses (role-filtered)
- `POST /courses` - Create course (Professor/Admin)
- `GET /courses/<id>` - Course details
- `PUT /courses/<id>` - Update course
- `DELETE /courses/<id>` - Delete course
- `POST /courses/<id>/enroll` - Student enrollment

### Tests & Assessment
- `GET /tests` - List tests
- `POST /tests` - Create test (Professor/Admin)
- `POST /tests/<id>/questions` - Add questions
- `POST /tests/<id>/submit` - Submit answers (Student)
- `GET /tests/<id>/results` - View results (Professor)

### Exercises
- `GET /exercises` - List exercises
- `POST /exercises` - Create exercise (Professor/Admin)
- `POST /exercises/<id>/submit` - Submit work (Student)

### Achievements
- `GET /badges` - List all badges
- `POST /badges` - Create badge (Professor/Admin)
- `POST /badges/assign` - Assign to student
- `GET /badges/student/achievements` - Student's badges

### Professor Tools
- `GET /professor/students` - List enrolled students
- `GET /professor/students/<id>` - Student progress
- `POST /professor/interventions` - Add notes
- `GET /professor/dashboard` - Dashboard stats

### Admin Management
- `GET /admin/users` - All users
- `POST /admin/users` - Create user
- `PUT /admin/users/<id>` - Update user
- `DELETE /admin/users/<id>` - Delete user
- `GET /admin/courses` - All courses
- `GET /admin/stats` - System statistics

### Chatbot
- `POST /chatbot/messages` - Save chat message
- `GET /chatbot/messages` - Chat history

### Health
- `GET /api/health` - System health check

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py
```

## 🔧 Role-Based Access Control

### Student Access
- View enrolled courses and exercises
- Take tests and submit answers
- View personal achievements
- Access chatbot

### Professor Access
- Create and manage courses
- Create tests and exercises
- View student progress and results
- Add intervention notes
- Assign badges to students

### Admin Access
- Full system access
- User management
- Course oversight
- System statistics

## 🏗️ Project Structure

```
edu-math-ai-back/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models
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
├── tests/                   # Unit tests
├── migrations/              # Database migrations
├── run.py                   # Application entry point
├── seed.py                  # Database seeding
├── requirements.txt         # Dependencies
└── .env.example            # Environment template
```

## 🚀 Deployment

### Render Deployment

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Use the following build command:
   ```bash
   pip install -r requirements.txt
   ```
4. Start command:
   ```bash
   python run.py
   ```

### Railway Deployment

1. Connect repository to Railway
2. Set environment variables
3. Railway will auto-detect Flask and deploy

### Environment Variables for Production

```env
FLASK_ENV=production
DATABASE_URL=your_neon_postgres_url
JWT_SECRET=your_secure_jwt_secret
PORT=5000
```

## 🔒 Security Features

- JWT token authentication
- bcrypt password hashing
- Role-based access control
- Input validation with Marshmallow
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration for frontend integration

## 🤝 Frontend Integration

This backend is designed to work with a React + Tailwind frontend supporting:

### Student Pages
- **Achievements**: View earned badges and progress
- **Exercises**: Interactive learning activities
- **Tests**: Take assessments and view scores
- **Profile**: Manage account settings

### Professor Pages
- **Dashboard**: Overview of courses and students
- **Courses**: Manage course content
- **Students**: Track student progress
- **Tests**: Create and review assessments

### Admin Pages
- **Users**: Manage all system users
- **Courses**: Oversee all courses
- **Analytics**: System-wide statistics

## 📈 Features

- ✅ Complete user management with three roles
- ✅ Course creation and enrollment system
- ✅ Test creation with multiple question types
- ✅ Interactive exercise system
- ✅ Achievement/badge system
- ✅ Professor intervention tracking
- ✅ AI chatbot message storage
- ✅ Comprehensive API documentation
- ✅ Role-based security
- ✅ Unit test coverage
- ✅ Production-ready deployment configuration

## 🆘 Troubleshooting

### Database Connection Issues
1. Verify Neon credentials in `.env`
2. Ensure SSL mode is enabled
3. Check firewall settings

### Migration Errors
```bash
# Reset migrations (development only)
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Token Issues
- Ensure JWT_SECRET is set and consistent
- Check token expiration settings
- Verify Authorization header format: `Bearer <token>`

## 📝 License

This project is licensed under the MIT License.
#   b a c k - e d u - m a t h - A I 
 
 