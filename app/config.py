import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://seo_user:seo_password@localhost:5432/seo_tracker'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis/Celery Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # API Keys
    SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
    
    # Email Configuration
    GMAIL_USER = os.environ.get('GMAIL_USER')
    GMAIL_PASSWORD = os.environ.get('GMAIL_PASSWORD')
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    
    # SEO Configuration
    TARGET_DOMAIN = os.environ.get('TARGET_DOMAIN', 'contentmastery.io')
    RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL')
    
    # Default Keywords - can be overridden via environment or database
    TARGET_KEYWORDS = [
        "make.com คือ",
        "favicon คือ", 
        "make.com",
        "content mastery",
        "เรียน seo ได้ใบ เซอร์ ฟรี",
        "semrush คือ",
        "คอร์สเรียน seo ฟรี",
        "ไอคอน fav",
        "make automation",
        "seo news",
        "semrush",
        "make com",
        "seo tools",
        "make.com คืออะไร",
        "make.com ราคา",
        "noindex tag",
        "seo",
        "semantic html",
        "favicon",
        "technical seo"
    ]
    
    # Search Configuration
    SEARCH_CONFIG = {
        'location': 'Thailand',
        'language': 'th',
        'country': 'th',
        'num_results': 100,
        'safe': 'off'
    }
    
    # Email Report Configuration
    EMAIL_CONFIG = {
        'sender_name': 'SEO Rank Tracker',
        'report_frequency': 'weekly',
        'timezone': 'UTC'
    }
    
    # Rate Limiting
    SERPAPI_RATE_LIMIT = 1.2  # seconds between requests