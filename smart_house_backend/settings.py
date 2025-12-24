import os
import dj_database_url  # ADDED FOR VERCEL
from pathlib import Path
from datetime import timedelta
import sys  # ADDED FOR VERCEL

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY',
                            'django-insecure-g&i8!boiz_q9_#!57n4rt!b@zhmub=r1d*ma+p^+plw22ev5@l')  # UPDATED

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'  # UPDATED
AUTH_USER_MODEL = 'users.User'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '.vercel.app',  # ADDED FOR VERCEL
    '.now.sh',  # ADDED FOR VERCEL
]

# Add your domain here if you have a custom domain
if os.environ.get('CUSTOM_DOMAIN'):  # ADDED FOR VERCEL
    ALLOWED_HOSTS.append(os.environ.get('CUSTOM_DOMAIN'))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'channels',
    'rest_framework',
    'corsheaders',
    # 'forestadmin.django_agent',

    # Local apps
    'users',
    'houses',
    'devices',
    'automation',
    'activities',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ADDED FOR VERCEL
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smart_house_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# WSGI for traditional HTTP
WSGI_APPLICATION = 'smart_house_backend.wsgi.application'

# ASGI for WebSocket support
ASGI_APPLICATION = 'smart_house_backend.asgi.application'

# Database - UPDATED FOR VERCEL
if os.environ.get('DATABASE_URL'):  # Production (Vercel with PostgreSQL)
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    print("⚡ Using PostgreSQL database from DATABASE_URL")
else:  # Development (local SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("💻 Using SQLite database for development")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files - UPDATED FOR VERCEL
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # ADDED FOR VERCEL

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# CORS settings for mobile app and frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React Native development
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # Django development server
    "http://127.0.0.1:8000",
    "https://*.vercel.app",  # ADDED FOR VERCEL
]

# CORS settings for Forest Admin
CORS_ALLOWED_ORIGIN_REGEXES = [
    r".*\.forestadmin\.com.*",
]
CORS_ALLOW_CREDENTIALS = True

# WebSocket and command timeout settings
COMMAND_TIMEOUT = 30  # seconds to wait for microcontroller ACK

# ============================================
# DYNAMIC SETTINGS BASED ON ENVIRONMENT
# ============================================

# Detect if running on Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1'

if IS_VERCEL:
    print("🚀 VERCEL PRODUCTION ENVIRONMENT DETECTED")

    # Force production settings
    DEBUG = False

    # Channels & WebSocket - DISABLED ON VERCEL (not supported)
    if 'channels' in INSTALLED_APPS:
        INSTALLED_APPS.remove('channels')
        print("⚠️ WebSockets disabled (not supported on Vercel)")

    # Use Redis if available for cache
    if os.environ.get('REDIS_URL'):
        print("🔗 Using Redis for caching")
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': os.environ.get('REDIS_URL'),
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'IGNORE_EXCEPTIONS': True,
                }
            }
        }
    else:
        # Use local memory cache on Vercel
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }

    # Security settings for production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

    # Channels configuration (empty on Vercel)
    CHANNEL_LAYERS = {}

else:
    print("💻 LOCAL DEVELOPMENT ENVIRONMENT")

    # Development Channels configuration
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

    # Development cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

    # Development security settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'smart_house.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django.channels': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'devices': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Fix for Vercel deployment - ensure WebSockets are disabled
if 'test' in sys.argv or 'vercel' in os.environ.get('HOST', ''):
    if 'channels' in INSTALLED_APPS:
        INSTALLED_APPS.remove('channels')
        CHANNEL_LAYERS = {}