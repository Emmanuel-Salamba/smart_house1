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
# PRODUCTION DEPLOYMENT SETTINGS - RENDER READY
# ============================================

# ============================================
# SECURITY & ENVIRONMENT SETTINGS
# ============================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if not os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes'):
        raise ValueError(
            "ERROR: SECRET_KEY environment variable is required in production. "
            "Set it in Render dashboard: Settings -> Environment Variables"
        )
    # For development only
    SECRET_KEY = 'django-insecure-dev-key-change-in-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
AUTH_USER_MODEL = 'users.User'

# Check if running on Render
IS_RENDER = os.environ.get('RENDER', 'false').lower() == 'true'

# ============================================
# HOST CONFIGURATION
# ============================================

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

# Render configuration
if IS_RENDER:
    ALLOWED_HOSTS.extend(['*.onrender.com'])
    # Static files will be served from the root
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    
# Add Fly.io if configured
FLY_APP_NAME = os.environ.get('FLY_APP_NAME')
if FLY_APP_NAME:
    ALLOWED_HOSTS.append(f'{FLY_APP_NAME}.fly.dev')

# Add Render external hostname if available (for custom domains)
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    if IS_RENDER:
        CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}']

# Add Vercel domains (for compatibility)
if os.environ.get('VERCEL') == '1':
    ALLOWED_HOSTS.extend(['.vercel.app', '.now.sh'])

# Add custom domain if specified
CUSTOM_DOMAIN = os.environ.get('CUSTOM_DOMAIN')
if CUSTOM_DOMAIN:
    ALLOWED_HOSTS.append(CUSTOM_DOMAIN)
    CSRF_TRUSTED_ORIGINS = CSRF_TRUSTED_ORIGINS if 'CSRF_TRUSTED_ORIGINS' in locals() else []
    CSRF_TRUSTED_ORIGINS.append(f'https://{CUSTOM_DOMAIN}')

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
# DATABASE CONFIGURATION - RENDER OPTIMIZED
# ============================================

# Get DATABASE_URL from environment (Render automatically provides this)
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Render provides 'postgres://', Django needs 'postgresql://'
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Parse the database URL
        DATABASES = {
            'default': dj_database_url.parse(
                database_url,
                conn_max_age=600,
                conn_health_checks=True,
            )
        }
        
        # Add production optimizations
        if not DEBUG:
            DATABASES['default']['CONN_MAX_AGE'] = 600
            DATABASES['default']['OPTIONS'] = {
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
            }
            
    except Exception as e:
        print(f"Database configuration error: {e}")
        print("Falling back to SQLite for development")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    # Development database
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
# STATIC & MEDIA FILES - RENDER OPTIMIZED
# ============================================

# Static files configuration (works for both Render and local)
STATIC_URL = '/static/'  # Always use leading slash for URL routing
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Include custom static files directory if it exists
STATICFILES_DIRS = [BASE_DIR / "static"] if os.path.isdir(BASE_DIR / "static") else []

# Whitenoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
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
        'rest_framework.authentication.SessionAuthentication',
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
# CORS SETTINGS - PRODUCTION READY
# ============================================

# Base CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Add production domains
if RENDER_EXTERNAL_HOSTNAME:
    CORS_ALLOWED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

if FLY_APP_NAME:
    CORS_ALLOWED_ORIGINS.append(f"https://{FLY_APP_NAME}.fly.dev")

if CUSTOM_DOMAIN:
    CORS_ALLOWED_ORIGINS.append(f"https://{CUSTOM_DOMAIN}")

# For development, allow all origins (adjust for production)
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOWED_ORIGINS = []  # Clear the list when allowing all
else:
    # Strict CORS for production
    CORS_ALLOW_ALL_ORIGINS = False

# Allow specific regex patterns
CORS_ALLOWED_ORIGIN_REGEXES = [
    r".*\.forestadmin\.com.*",
]

# Add Render subdomains
if IS_RENDER:
    CORS_ALLOWED_ORIGIN_REGEXES.append(r"https://.*\.onrender\.com")

CORS_ALLOW_CREDENTIALS = True

# ============================================
# REDIS & CACHE CONFIGURATION
# ============================================

# Get Redis URL (Render Redis addon provides REDIS_URL)
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Fix Redis URL format if needed
if REDIS_URL and not REDIS_URL.startswith('redis://'):
    REDIS_URL = f'redis://{REDIS_URL}:6379'

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

# ============================================
# CHANNELS & WEBSOCKET CONFIGURATION
# ============================================

# Use Redis if available, otherwise in-memory for development
if REDIS_URL and REDIS_URL != 'redis://localhost:6379':
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [REDIS_URL],
                "capacity": 1500,
                "expiry": 10,
            },
        },
    }
else:
    # Development/fallback channel layer
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer'
        }
    }

# ============================================
# SECURITY SETTINGS
# ============================================

# WebSocket and command timeout settings
COMMAND_TIMEOUT = 30

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Ensure CSRF trusted origins are set
    if 'CSRF_TRUSTED_ORIGINS' not in locals():
        CSRF_TRUSTED_ORIGINS = []
    
    # Add all HTTPS origins from CORS_ALLOWED_ORIGINS
    for origin in CORS_ALLOWED_ORIGINS:
        if origin.startswith('https://'):
            CSRF_TRUSTED_ORIGINS.append(origin)
    
    # Add regex origins that are HTTPS
    for regex in CORS_ALLOWED_ORIGIN_REGEXES:
        if 'https://' in regex:
            CSRF_TRUSTED_ORIGINS.append(regex)
else:
    # Development security settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    CSRF_TRUSTED_ORIGINS = []  # Clear for development

# ============================================
# LOGGING CONFIGURATION - RENDER OPTIMIZED
# ============================================

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
            'stream': sys.stdout,  # Render captures stdout
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',  # Reduce SQL log noise in production
            'propagate': False,
        },
        'django.channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'devices': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
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

if 'test' in sys.argv or 'pytest' in sys.argv[0]:
    # Use SQLite for tests
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
    # Disable caching for tests
    CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
    # Use in-memory channel layer for tests
    CHANNEL_LAYERS['default']['BACKEND'] = 'channels.layers.InMemoryChannelLayer'
    # Disable security for tests
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ============================================
# HEALTH CHECK SETTINGS FOR RENDER
# ============================================

# Render health check endpoint (if you add it to urls.py)
HEALTH_CHECK_ENABLED = IS_RENDER

print(f"=== Django Settings ===")
print(f"Debug mode: {DEBUG}")
print(f"Running on Render: {IS_RENDER}")
print(f"Allowed hosts: {ALLOWED_HOSTS}")
print(f"Database engine: {DATABASES['default'].get('ENGINE', 'unknown')}")
print(f"Static root: {STATIC_ROOT}")
print(f"========================")