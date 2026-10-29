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

from nika.backend.database import database_config

DATABASES = {'default': database_config(BASE_DIR)}

TEMPLATES = []
USE_TZ = True
TIME_ZONE = 'UTC'
