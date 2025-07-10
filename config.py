import os
from datetime import timedelta

class Config:
    # General Flask secret key
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")

    # SQLAlchemy MySQL connection URI
    # Example uses:
    #   user: root
    #   password: rootpass
    #   host: localhost
    #   database: smart_task_db
    #
    # Adjust as needed.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:admin@localhost/smart_task_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
