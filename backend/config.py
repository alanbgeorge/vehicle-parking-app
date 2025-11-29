import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask / DB
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "parking_system.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "change-this-secret-key"

    # Redis + Celery
    REDIS_URL = "redis://localhost:6379/0"
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # MailHog SMTP
    MAIL_SERVER = "localhost"
    MAIL_PORT = 1025
    FROM_EMAIL = "noreply@parkingapp.com"
