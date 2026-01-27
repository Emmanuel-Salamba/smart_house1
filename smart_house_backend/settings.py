import os
import dj_database_url
from pathlib import Path
from datetime import timedelta
import sys
from dotenv import load_dotenv
load_dotenv()  

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# PRODUCTION DEPLOYMENT SETTINGS
# ============================================
# This project supports deployment on Render, Fly.io, Railway, and other platforms
# For Render deployment, Render automatically sets: DATABASE_URL, REDIS_URL, RENDER_EXTERNAL_HOSTNAME

# ============================================
# SECURITY & ENVIRONMENT SETTINGS
# ============================================

# SECURITY WARNING: keep the secret key used in production secret!
# MUST be set via environment variable in production
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if not os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes'):
        raise ValueError(
            "ERROR: SECRET_KEY environment variable is required in production. "
            "Set it before deploying to Railway or other production environments."
        )
    # For development only
    SECRET_KEY = 'django-insecure-dev-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
AUTH_USER_MODEL = 'users.User'

# ============================================
# HOST CONFIGURATION
# ============================================

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '*.fly.dev',         # Fly.io domains
    '*.onrender.com',    # Render domains
]

# Add Fly.io hostname if available
FLY_APP_NAME = os.environ.get('FLY_APP_NAME')
if FLY_APP_NAME:
    ALLOWED_HOSTS.append(f'{FLY_APP_NAME}.fly.dev')

# Add Render external hostname if available
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Add Vercel domains (for compatibility)
if os.environ.get('VERCEL') == '1':
    ALLOWED_HOSTS.extend(['.vercel.app', '.now.sh'])

# Add custom domain if specified
if os.environ.get('CUSTOM_DOMAIN'):
    ALLOWED_HOSTS.append(os.environ.get('CUSTOM_DOMAIN'))

# ============================================
# APPLICATION DEFINITION
# ============================================

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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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

# ============================================
# WSGI/ASGI CONFIGURATION
# ============================================

WSGI_APPLICATION = 'smart_house_backend.wsgi.application'
ASGI_APPLICATION = 'smart_house_backend.asgi.application'

# ============================================
# DATABASE CONFIGURATION - FIXED VERSION
# ============================================

# Get DATABASE_URL from environment
database_url = os.environ.get('DATABASE_URL')

if database_url and 'postgresql://' in database_url:
    # FORCE PostgreSQL when DATABASE_URL is a PostgreSQL URL
    try:
        # Parse the URL and ensure it's PostgreSQL
        db_config = dj_database_url.parse(database_url, conn_max_age=600)
        
        # Force PostgreSQL engine explicitly
        db_config['ENGINE'] = 'django.db.backends.postgresql'
        
        DATABASES = {
            'default': db_config
        }
        
    except Exception as e:
        # Fallback to SQLite on error
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
        
else:
    # Fallback to SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================
# PASSWORD VALIDATION
# ============================================

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

# ============================================
# INTERNATIONALIZATION
# ============================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ============================================
# STATIC & MEDIA FILES
# ============================================

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============================================
# DEFAULT PRIMARY KEY FIELD TYPE
# ============================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# REST FRAMEWORK CONFIGURATION
# ============================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For admin interface
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# ============================================
# JWT SETTINGS
# ============================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ============================================
# CORS SETTINGS
# ============================================

# Base CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# For development, allow all origins (adjust for production)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # Production CORS settings - Add your actual frontend domains here
    production_domains = [
        "https://your-flutter-app-domain.com",  # Replace with your Flutter app domain
    ]
    CORS_ALLOWED_ORIGINS.extend(production_domains)
    
    # Add Fly.io domain if configured
    if FLY_APP_NAME:
        CORS_ALLOWED_ORIGINS.append(f"https://{FLY_APP_NAME}.fly.dev")
    
    # Add Render domain if configured
    if RENDER_EXTERNAL_HOSTNAME:
        CORS_ALLOWED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# CORS settings for Forest Admin
CORS_ALLOWED_ORIGIN_REGEXES = [
    r".*\.forestadmin\.com.*",
]

CORS_ALLOW_CREDENTIALS = True

# ============================================
# REDIS & CACHE CONFIGURATION
# ============================================

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# ============================================
# CHANNELS & WEBSOCKET CONFIGURATION
# ============================================

# Render supports WebSockets with Redis backend
# Use Redis channel layer for production
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

# ============================================
# SECURITY SETTINGS
# ============================================

# WebSocket and command timeout settings
COMMAND_TIMEOUT = 30  # seconds to wait for microcontroller ACK

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
else:
    # Development security settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ============================================
# LOGGING CONFIGURATION
# ============================================
# For Render: Only console logging is recommended (persists in logs)
# File logging in /tmp is temporary and will be lost

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'devices': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'users': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'activities': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================
# TEST ENVIRONMENT CONFIGURATION
# ============================================

if 'test' in sys.argv:
    # Use SQLite for tests
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
    # Disable caching for tests
    CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
    # Use in-memory channel layer for tests
    CHANNEL_LAYERS['default']['BACKEND'] = 'channels.layers.InMemoryChannelLayer'
