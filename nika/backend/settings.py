import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

SECRET_KEY = os.environ.get('NIKA_BACKEND_SECRET_KEY', 'dev-only-nika-backend-secret-key')
DEBUG = os.environ.get('NIKA_BACKEND_DEBUG', '1') == '1'
ALLOWED_HOSTS = os.environ.get('NIKA_BACKEND_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
ROOT_URLCONF = 'nika.backend.urls'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'nika.backend.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

DATABASES = {
    # Temporary SQLite default so Django commands can run before the real app database is chosen.
    # Strategy endpoints intentionally stay unimplemented until the database schema exists.
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

TEMPLATES = []
USE_TZ = True
TIME_ZONE = 'UTC'
