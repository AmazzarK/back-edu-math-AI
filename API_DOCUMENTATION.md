# EduMath AI Platform - API Documentation v3.0

## Overview

The Educational Mathematics AI Platform is a comprehensive backend system that provides AI-powered tutoring, class management, file handling, and analytics for mathematics education.

## New Features in Version 3.0

### 🤖 AI-Powered Tutoring
- **Real-time chat with AI tutor**
- **Context-aware exercise help**
- **Conversation history and persistence**
- **Educational context integration**

### 🏫 Class Management
- **Create and manage classes**
- **Student enrollment via class codes**
- **Assignment distribution**
- **Class analytics and progress tracking**

### 📁 File Management
- **Multi-format file uploads**
- **Local and S3 storage options**
- **Image processing and optimization**
- **File sharing and access control**

### 📊 Advanced Dashboard
- **Role-based dashboards (Student/Professor/Admin)**
- **Real-time analytics and charts**
- **Progress tracking and insights**
- **Performance metrics**

### 🔔 Notification System
- **Real-time notifications**
- **Email integration with Celery**
- **Customizable notification preferences**
- **Assignment reminders and updates**

## API Endpoints

### Authentication
```
POST   /api/auth/register    - User registration
POST   /api/auth/login       - User login
POST   /api/auth/refresh     - Refresh JWT token
POST   /api/auth/logout      - User logout
```

### AI Chat System
```
GET    /api/chat/conversations              - Get user conversations
POST   /api/chat/conversations              - Create new conversation
GET    /api/chat/conversations/{id}         - Get conversation details
PUT    /api/chat/conversations/{id}         - Update conversation
DELETE /api/chat/conversations/{id}         - Delete conversation
POST   /api/chat/message                    - Send chat message
GET    /api/chat/suggestions                - Get conversation suggestions
GET    /api/chat/analytics                  - Get chat analytics
POST   /api/chat/exercise/{id}/help         - Get exercise-specific help
```

### Class Management
```
GET    /api/classes                         - Get user's classes
POST   /api/classes                         - Create new class (professors)
GET    /api/classes/{id}                    - Get class details
PUT    /api/classes/{id}                    - Update class
DELETE /api/classes/{id}                    - Delete class
POST   /api/classes/{id}/enrollment         - Enroll in class
DELETE /api/classes/{id}/enrollment         - Unenroll from class
POST   /api/classes/enroll                  - Enroll via class code
POST   /api/classes/{id}/assignments        - Assign exercise to class
GET    /api/classes/{id}/students           - Get class students
GET    /api/classes/{id}/statistics         - Get class statistics
```

### Dashboard & Analytics
```
GET    /api/dashboard                       - Get role-based dashboard
GET    /api/dashboard/student               - Student dashboard
GET    /api/dashboard/professor             - Professor dashboard
GET    /api/dashboard/admin                 - Admin dashboard
GET    /api/dashboard/quick-stats           - Quick statistics summary
GET    /api/dashboard/analytics             - Detailed analytics
GET    /api/dashboard/charts                - Chart data for visualizations
```

### File Management
```
POST   /api/files/upload                    - Upload file
GET    /api/files                           - Get user's files
GET    /api/files/{id}                      - Get file details
DELETE /api/files/{id}                      - Delete file
GET    /api/files/{id}/download             - Download file
GET    /api/files/{id}/url                  - Get file access URL
GET    /api/files/stats                     - Get storage statistics
POST   /api/files/bulk                      - Bulk file operations
POST   /api/files/validate                  - Validate file before upload
```

### Notifications
```
GET    /api/notifications                   - Get user notifications
PUT    /api/notifications/{id}              - Mark notification as read
DELETE /api/notifications/{id}              - Delete notification
PUT    /api/notifications/bulk              - Mark all as read
GET    /api/notifications/stats             - Get notification statistics
GET    /api/notifications/unread-count      - Get unread count
GET    /api/notifications/preferences       - Get notification preferences
PUT    /api/notifications/preferences       - Update preferences
POST   /api/notifications/admin             - Create system notification (admin)
DELETE /api/notifications/admin             - Cleanup old notifications (admin)
GET    /api/notifications/types             - Get notification types
```

### Existing Endpoints
```
GET    /api/exercises                       - Get exercises
POST   /api/exercises                       - Create exercise
GET    /api/exercises/{id}                  - Get exercise details
PUT    /api/exercises/{id}                  - Update exercise
DELETE /api/exercises/{id}                  - Delete exercise
POST   /api/progress                        - Submit progress
GET    /api/progress                        - Get user progress
GET    /api/analytics/overview              - Get analytics overview
```

## Request/Response Examples

### AI Chat Message
```json
POST /api/chat/message
{
  "message": "Can you help me with quadratic equations?",
  "context_type": "general",
  "context_data": {}
}

Response:
{
  "success": true,
  "data": {
    "conversation_id": 123,
    "user_message": {...},
    "ai_response": {...},
    "conversation_title": "Quadratic Equations Help"
  }
}
```

### Create Class
```json
POST /api/classes
{
  "name": "Advanced Algebra",
  "description": "Advanced topics in algebra",
  "subject": "Mathematics",
  "grade_level": 10,
  "max_students": 30
}

Response:
{
  "success": true,
  "data": {
    "id": 456,
    "name": "Advanced Algebra",
    "class_code": "ALG123",
    "professor_id": "prof_123",
    ...
  }
}
```

### File Upload
```bash
POST /api/files/upload
Content-Type: multipart/form-data

file: [binary data]
storage_type: "local"
description: "Math homework solutions"
```

### Dashboard Data
```json
GET /api/dashboard/student

Response:
{
  "success": true,
  "data": {
    "student_info": {...},
    "quick_stats": {
      "total_exercises_completed": 45,
      "average_score": 87.5,
      "current_streak": 7,
      "total_classes": 3
    },
    "recent_progress": [...],
    "enrolled_classes": [...],
    "achievements": {...}
  }
}
```

## Authentication

All API endpoints (except registration and login) require JWT authentication:

```bash
Authorization: Bearer <jwt_token>
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "errors": {...}  // For validation errors
}
```

## Rate Limiting

- Default: 1000 requests per hour per user
- File uploads: 100 requests per hour
- AI chat: 500 requests per hour

## File Upload Limits

- **Images**: 10MB max (jpg, png, gif, bmp, webp)
- **Documents**: 50MB max (pdf, doc, docx, txt, rtf)
- **Archives**: 200MB max (zip, tar, gz, rar)
- **Code files**: 5MB max (py, js, html, css, json, xml)

## Environment Variables

Key environment variables for new features:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo

# File Storage
UPLOAD_FOLDER=uploads
AWS_ACCESS_KEY_ID=your-aws-key
S3_BUCKET_NAME=your-bucket

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/0

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
```

## WebSocket Events (Future)

The platform is designed to support real-time features:

- `chat_message` - New chat messages
- `notification` - Real-time notifications
- `class_update` - Class activity updates
- `progress_update` - Real-time progress updates

## Security Features

- **JWT Authentication** with refresh tokens
- **Role-based access control** (Student/Professor/Admin)
- **File type validation** and size limits
- **Input sanitization** and validation
- **Rate limiting** per endpoint
- **CORS protection**
- **SQL injection prevention**

## Caching Strategy

- **Redis caching** for frequently accessed data
- **Dashboard data**: 10-15 minutes
- **User stats**: 5 minutes
- **File metadata**: 1 hour
- **AI conversation context**: 30 minutes

## Background Tasks

Celery tasks for asynchronous operations:
- **Email notifications**
- **File processing**
- **Analytics computation**
- **Assignment reminders**
- **Weekly progress reports**

## Monitoring and Logging

- **Structured logging** with different levels
- **API call tracking** and performance metrics
- **Error monitoring** and alerting
- **User activity tracking**
- **File access logging**

## Deployment Considerations

### Production Checklist
- [ ] Set secure `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching and Celery
- [ ] Configure OpenAI API access
- [ ] Set up email service (SMTP)
- [ ] Configure AWS S3 (optional)
- [ ] Enable HTTPS and secure cookies
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Set up Celery workers and beat scheduler

### Scaling Recommendations
- **Database**: Use connection pooling and read replicas
- **Caching**: Redis cluster for high availability
- **File Storage**: S3 or distributed storage
- **AI Services**: OpenAI API with retry logic
- **Background Tasks**: Multiple Celery workers
- **Load Balancing**: nginx or cloud load balancer

## Testing

Run the test suite:
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# API tests
python -m pytest tests/api/
```

## Support

For questions or issues:
- **Documentation**: `/api/info` endpoint
- **Health Check**: `/health` endpoint
- **API Status**: Real-time status monitoring
