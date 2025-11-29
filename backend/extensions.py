# backend/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import redis

db = SQLAlchemy()
bcrypt = Bcrypt()

# Global Redis client
redis_client_a = None


def init_redis_a(app):

    global redis_client_a

    redis_client_a = redis.Redis.from_url(
        app.config["REDIS_URL"],
        decode_responses=True,   # ensures strings instead of bytes
    )


def get_redis():

    global redis_client_a
    if redis_client_a is None:
        raise RuntimeError("Redis not initialized. Call init_redis_a(app) first.")
    return redis_client_a


# ---------------------------------------------
# SIMPLE REDIS CACHE HELPERS
# ---------------------------------------------

def cache_set(key, value, ex=60):

    redis_client = get_redis()
    redis_client.set(key, value, ex=ex)


def cache_get(key):

    redis_client = get_redis()
    return redis_client.get(key)


import smtplib
from email.mime.text import MIMEText
from flask import current_app

def send_email(to_email, subject, body):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = current_app.config["FROM_EMAIL"]
    msg["To"] = to_email

    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"],
        current_app.config["MAIL_PORT"]
    ) as server:
        server.sendmail(
            current_app.config["FROM_EMAIL"],
            [to_email],
            msg.as_string()
        )
