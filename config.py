import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    LOG_LEVEL = 'INFO'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY') or 'csrf-secret-key'
    # Use Redis for rate limiting if available, otherwise memory
    redis_url = os.environ.get('REDIS_URL')
    if redis_url and redis_url != 'redis://localhost:6379':
        RATELIMIT_STORAGE_URI = redis_url
    else:
        RATELIMIT_STORAGE_URI = 'memory://'
    CELERY_BROKER_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
    # Cache configuration moved to extensions.py for conditional setup

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    LOG_LEVEL = 'WARNING'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
