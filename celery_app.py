"""
Celery application entry point
This file is used to start Celery workers and beat scheduler
"""
from app.tasks import celery

if __name__ == '__main__':
    celery.start()