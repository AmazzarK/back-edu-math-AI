"""
Celery configuration for the Educational Mathematics AI Platform.
"""
import os
from celery import Celery
from celery.schedules import crontab

def make_celery(app=None):
    """Create and configure Celery instance."""
    celery = Celery(
        'edumath-ai',
        broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
        include=['app.tasks.email_tasks']
    )
    
    # Update configuration
    celery.conf.update(
        # Basic settings
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Task execution settings
        task_always_eager=False,
        task_eager_propagates=True,
        task_ignore_result=False,
        task_store_eager_result=True,
        
        # Worker settings
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_disable_rate_limits=False,
        
        # Result backend settings
        result_expires=3600,  # 1 hour
        result_backend_transport_options={
            'retry_on_timeout': True,
            'retry_on_error': [ConnectionError, TimeoutError],
        },
        
        # Broker settings
        broker_transport_options={
            'retry_on_timeout': True,
            'retry_on_error': [ConnectionError, TimeoutError],
        },
        
        # Security
        worker_hijack_root_logger=False,
        worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s',
        
        # Periodic tasks (Celery Beat)
        beat_schedule={
            'send-assignment-reminders': {
                'task': 'app.tasks.email_tasks.send_assignment_reminder_emails',
                'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
            },
            'send-weekly-progress-reports': {
                'task': 'app.tasks.email_tasks.weekly_tasks',
                'schedule': crontab(hour=10, minute=0, day_of_week=0),  # Sundays at 10 AM
            },
            'cleanup-old-notifications': {
                'task': 'app.tasks.email_tasks.cleanup_old_email_logs',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
        },
        beat_schedule_filename='celerybeat-schedule',
    )
    
    if app:
        # Update configuration with Flask app config
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            """Make celery tasks work with Flask app context."""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# Create default Celery instance
celery = make_celery()
