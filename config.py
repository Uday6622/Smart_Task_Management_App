import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:dCzDFijPoQnKuggYMpnHxEvSFTtVBYTI@maglev.proxy.rlwy.net:36248/railway"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
