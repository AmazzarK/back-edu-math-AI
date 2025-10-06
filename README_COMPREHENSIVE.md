# EduMath AI Platform - Backend

A comprehensive, production-ready Flask backend for an Educational Mathematics AI Platform. This system provides AI-powered tutoring, class management, file handling, notifications, and advanced analytics for educational institutions.

## 🌟 Features

### 🤖 AI-Powered Learning
- **Intelligent Tutoring**: OpenAI-powered chat system with educational context
- **Conversation Management**: Persistent chat sessions with context awareness
- **Mock AI Provider**: Fallback system for development and testing

### 🏫 Class Management
- **Course Creation**: Professors can create and manage mathematics courses
- **Enrollment System**: Students join classes using unique enrollment codes
- **Assignment Distribution**: Automated exercise assignment to enrolled students
- **Progress Tracking**: Comprehensive analytics for student performance

### 📁 File Management
- **Multi-Storage Support**: Local filesystem and AWS S3 integration
- **File Type Validation**: Secure upload with type and size restrictions
- **Image Processing**: Automatic image optimization and thumbnail generation
- **Access Control**: Role-based file access permissions

### 🔔 Notification System
- **Email Integration**: SMTP-based email notifications
- **Background Processing**: Celery-powered async email delivery
- **User Preferences**: Customizable notification settings
- **Automated Alerts**: Welcome emails, progress reports, assignment reminders

### 📊 Advanced Analytics
- **Role-Based Dashboards**: Customized views for admins, professors, and students
- **Performance Metrics**: Detailed analytics on learning progress
- **Visual Charts**: Data visualization for better insights
- **Weekly Reports**: Automated progress summaries

### 🔐 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: Admin, Professor, and Student roles
- **Input Validation**: Comprehensive request validation
- **Security Headers**: CORS, rate limiting, and security best practices

## 🛠️ Technology Stack

- **Framework**: Flask + Flask-RESTful
- **Database**: PostgreSQL (SQLite for development)
- **Caching**: Redis
- **Task Queue**: Celery
- **Authentication**: JWT (Flask-JWT-Extended)
- **AI Integration**: OpenAI API
- **File Storage**: Local filesystem + AWS S3
- **Email**: SMTP with HTML templates
- **Deployment**: Docker + Docker Compose

## 📋 Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL (for production)
- Redis (for caching and task queue)
- SMTP server (for email notifications)

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd edu-math-ai-back
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Deploy with Docker**
```bash
# Development environment
chmod +x deploy.sh
./deploy.sh development

# Production environment
./deploy.sh production
```

4. **Access the application**
- API: http://localhost:5000
- Health Check: http://localhost:5000/health
- API Documentation: See `API_DOCUMENTATION.md`

### Option 2: Local Development

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize database**
```bash
python db_manager.py seed
```

5. **Start the application**
```bash
python run.py
```

6. **Start background workers (optional)**
```bash
# In separate terminals
celery -A celery_app.celery worker --loglevel=info
celery -A celery_app.celery beat --loglevel=info
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/edumath_ai
# or for development:
# DATABASE_URL=sqlite:///edumath_ai.db

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# AWS S3 (optional)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_BUCKET=your-s3-bucket-name
AWS_REGION=us-east-1

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# File Upload
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=uploads
```

### Database Management

```bash
# Initialize database with sample data
python db_manager.py seed

# Create admin user
python db_manager.py admin

# Show database statistics
python db_manager.py stats

# Reset database (WARNING: deletes all data)
python db_manager.py reset
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python test_runner.py all

# Run specific test types
python test_runner.py unit
python test_runner.py api
python test_runner.py coverage
python test_runner.py quality

# Clean test artifacts
python test_runner.py clean
```

### Sample Accounts (Development)

After running `python db_manager.py seed`:

- **Admin**: admin@edumath-ai.com / admin123
- **Professor**: prof1@edumath-ai.com / professor123
- **Student**: student1@edumath-ai.com / student123

## 📚 API Documentation

Comprehensive API documentation is available in `API_DOCUMENTATION.md`, including:

- Authentication endpoints
- User management
- Exercise and progress tracking
- AI chat integration
- Class management
- File upload/download
- Notification system
- Dashboard analytics

### Key Endpoints

```
# Authentication
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh

# AI Chat
POST /api/chat/start
POST /api/chat/{conversation_id}/message

# Classes
GET /api/classes/
POST /api/classes/
POST /api/classes/{class_id}/enroll

# Dashboard
GET /api/dashboard/stats
GET /api/dashboard/analytics

# Files
POST /api/files/upload
GET /api/files/{file_id}/download

# Notifications
GET /api/notifications/
POST /api/notifications/preferences
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Useful Docker Commands
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Clean up
docker-compose down -v
docker system prune -f
```

## 📁 Project Structure

```
edu-math-ai-back/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── extensions.py            # Flask extensions
│   ├── models.py               # Database models
│   ├── api/                    # API endpoints
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── classes.py
│   │   ├── dashboard.py
│   │   ├── files.py
│   │   └── notifications.py
│   ├── services/               # Business logic
│   │   ├── ai_provider.py
│   │   ├── chat.py
│   │   ├── class_management.py
│   │   ├── dashboard.py
│   │   ├── file_upload.py
│   │   └── notification.py
│   ├── tasks/                  # Background tasks
│   │   └── email_tasks.py
│   └── utils/                  # Utilities
│       ├── decorators.py
│       └── validators.py
├── migrations/                 # Database migrations
├── uploads/                   # File uploads (local)
├── logs/                     # Application logs
├── tests/                    # Test suite
├── docker-compose.yml        # Docker development
├── docker-compose.prod.yml   # Docker production
├── Dockerfile               # Docker image
├── requirements.txt         # Python dependencies
├── run.py                  # Application entry point
├── db_manager.py           # Database management
├── test_runner.py          # Test runner
├── deploy.sh              # Deployment script
├── celery_app.py          # Celery configuration
└── .env.example           # Environment template
```

## 🔒 Security Considerations

### Production Checklist

- [ ] Change all default passwords
- [ ] Use strong, unique secret keys
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable application logging
- [ ] Configure rate limiting
- [ ] Review CORS settings
- [ ] Set up monitoring and alerts

### Security Features

- JWT token authentication with expiration
- Role-based access control
- Input validation and sanitization
- File upload restrictions
- SQL injection prevention
- CORS protection
- Security headers
- Rate limiting

## 📈 Monitoring & Logging

### Application Logs
```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log
```

### Health Checks
- Endpoint: `GET /health`
- Docker health checks included
- Database connectivity validation
- Redis connection verification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:

1. Check the API documentation
2. Review the logs
3. Consult the troubleshooting section
4. Create an issue on GitHub

## 🔮 Future Enhancements

- WebSocket integration for real-time features
- Advanced AI model fine-tuning
- Mobile app API extensions
- Advanced analytics and reporting
- Multi-language support
- LTI (Learning Tools Interoperability) integration
