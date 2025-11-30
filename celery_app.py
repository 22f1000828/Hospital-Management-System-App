from celery import Celery
from celery.schedules import crontab
from app import create_app
from config import Config

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Asia/Kolkata',
        enable_utc=False,
        task_track_started=True,
        task_time_limit=30 * 60,
        task_soft_time_limit=25 * 60,
        beat_schedule={
            'daily-reminders': {
                'task': 'app.tasks.send_daily_reminders',
                'schedule': crontab(hour=20, minute=13),
            },
            'monthly-reports': {
                'task': 'app.tasks.generate_monthly_reports_for_all_users',
                'schedule': crontab(day_of_month=30, hour=20, minute=13),
            },
        },
    )
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    return celery

flask_app = create_app(Config)
celery = make_celery(flask_app)

from app.tasks import register_tasks
register_tasks(celery)

