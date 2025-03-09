import os
from pathlib import Path

from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-r@6bz8ef@g+(^f@_@dyy9xg@1-uq(n@o@29yy)!jku=mq8dfro'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'website',
    'django_prometheus',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'website.middlewares.cart_middleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

STATIC_URL = 'static/'

# STATIC_ROOT = os.path.join(BASE_DIR, 'static')


STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)

ROOT_URLCONF = 'djangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'djangoProject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

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

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'sss30112001@yandex.ru'
EMAIL_HOST_PASSWORD = 'ksqyacpehtlnguof'

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER

MANAGERS = (('Sergecho', 'sss30112001@yandex.ru'),)

CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STEAM_KEY = "6B85973E0AD769609FD41EA8D1888028"

CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_BEAT_SCHEDULE = {
    "load_steam_ids": {
        "task": "website.tasks.load_steam_ids",
        "schedule": crontab(minute=5),
    },
    "import_games": {
        "task": "website.tasks.import_games",
        "schedule": crontab(minute=20),
    },
    "import_steam_prices": {
        "task": "website.tasks.import_steam_prices",
        "schedule": crontab(minute=0, hour=10),
    },
    "import_plati_prices": {
        "task": "website.tasks.import_plati_prices",
        "schedule": crontab(minute=0, hour=10),
    },
    "apply_rules": {
        "task": "website.tasks.apply_rules",
        "schedule": crontab(minute=50),
    },
    "delete_outdated_rules": {
        "task": "website.tasks.delete_outdated_rules",
        "schedule": crontab(minute=30),
    },
}

STEAM_CONCURRENT_NAME = 'Steam'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] {%(module)s} [%(levelname)s] - %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'loki': {
            'level': 'INFO',
            'class': 'logging_loki.LokiHandler',
            'url': f"http://localhost:3100/loki/api/v1/push",
            'tags': {"app": "web", },
            'version': "1",
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['loki', 'console', ],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
