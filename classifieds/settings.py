import os
import json
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()

# Basic flags
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'replace-this-secret-key')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'  # Default to True for local development
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Environment mode (set to 'True' in Cloud Run/production)
DJANGO_PRODUCTION = os.environ.get('DJANGO_PRODUCTION', 'False') == 'True'
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_yasg',

    'apps.common',
    'apps.users',
    'apps.products',
    'apps.payments',
    'apps.reviews',
    'apps.chats',
    'apps.notifications',
    'apps.reports',
    'apps.chatbot',
    'apps.wishlist',
]

# Add storages app when using cloud storage
if DJANGO_PRODUCTION:
    INSTALLED_APPS.append('storages')

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'classifieds.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'classifieds.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Allow configuring the database via a single DATABASE_URL environment variable
# e.g. postgres://user:pass@host:port/dbname?sslmode=require
import urllib.parse as urlparse

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    url = urlparse.urlparse(DATABASE_URL)
    db_name = url.path[1:] if url.path and len(url.path) > 1 else ''
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_name,
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port,
        }
    }
    # parse query string for additional options like sslmode
    qs = dict(urlparse.parse_qsl(url.query))
    if 'sslmode' in qs:
        DATABASES['default']['OPTIONS'] = {'sslmode': qs['sslmode']}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Add STATICFILES_DIRS if you have a general static folder
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Media configuration: local by default, Google Cloud Storage in production
if DJANGO_PRODUCTION:
    # Use django-storages with Google Cloud Storage
    DEFAULT_FILE_STORAGE = os.environ.get('DEFAULT_FILE_STORAGE', 'storages.backends.gcloud.GoogleCloudStorage')
    GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
    GS_PROJECT_ID = os.environ.get('GS_PROJECT_ID')
    GS_DEFAULT_ACL = 'publicRead'
    # Allow providing credentials via JSON in env var or via GOOGLE_APPLICATION_CREDENTIALS
    GS_CREDENTIALS_JSON = os.environ.get('GS_CREDENTIALS_JSON')
    if GS_CREDENTIALS_JSON:
        try:
            from google.oauth2 import service_account
            creds_info = json.loads(GS_CREDENTIALS_JSON)
            GS_CREDENTIALS = service_account.Credentials.from_service_account_info(creds_info)
        except Exception:
            GS_CREDENTIALS = None
    else:
        GS_CREDENTIALS = None

    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
    MEDIA_ROOT = os.path.join(str(BASE_DIR), 'media')
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.normpath(str(BASE_DIR / 'media'))
# Always expose GS_BUCKET_NAME to the app so URL fallback can use it
GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
}

# CORS Configuration - Use explicit allowed origins from environment
# Set CORS_ALLOWED_ORIGINS env var as comma-separated list for production
# e.g., CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com
CORS_ALLOWED_ORIGINS_RAW = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if CORS_ALLOWED_ORIGINS_RAW:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS_RAW.split(',') if origin.strip()]
    CORS_ALLOW_ALL_ORIGINS = False
else:
    # Development fallback - allow localhost origins
    CORS_ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
    ]
    CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all in debug mode

# CSRF Configuration
CSRF_TRUSTED_ORIGINS_RAW = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if CSRF_TRUSTED_ORIGINS_RAW:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in CSRF_TRUSTED_ORIGINS_RAW.split(',') if origin.strip()]
else:
    # Development fallback
    CSRF_TRUSTED_ORIGINS = [
        'http://localhost:5173',
        'http://localhost:5174',
        'http://localhost:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000',
    ]

# Email Configuration
# Using console backend for development - emails are printed to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'Eagerly <noreply@eagerly.com>'
