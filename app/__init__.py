from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
import os

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Initialize extensions
    from app.models import db
    db.init_app(app)
    
    migrate = Migrate(app, db)
    
    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        
        # Initialize default keywords if none exist
        from app.models import Keyword
        from app.config import Config
        
        if Keyword.query.count() == 0:
            target_domain = app.config.get('TARGET_DOMAIN', 'yourwebsite.com')
            for keyword_text in Config.TARGET_KEYWORDS:
                keyword = Keyword(
                    keyword=keyword_text,
                    domain=target_domain,
                    is_active=True
                )
                db.session.add(keyword)
            db.session.commit()
    
    return app

def create_celery_app(app=None):
    """Create and configure Celery app"""
    from celery import Celery
    from app.config import Config
    
    celery = Celery('seo_tracker')
    celery.conf.update(
        broker_url=Config.REDIS_URL,
        result_backend=Config.REDIS_URL,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        beat_schedule={
            'weekly-rank-check': {
                'task': 'app.tasks.weekly_rank_check',
                'schedule': {
                    'minute': 0,
                    'hour': 9,
                    'day_of_week': 1,  # Monday
                },
            },
            'cleanup-old-data': {
                'task': 'app.tasks.cleanup_old_data',
                'schedule': {
                    'minute': 0,
                    'hour': 2,
                    'day_of_week': 0,  # Sunday
                },
            },
        }
    )
    
    return celery