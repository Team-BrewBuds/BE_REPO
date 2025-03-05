import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env.str("SECRET_KEY", "test")

LOCAL_APPS = [
    "repo",
    "repo.profiles",
    "repo.beans",
    "repo.records",
    "repo.search",
    "repo.recommendation",
    "repo.common",
    "repo.interactions",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "django.contrib.sites",
    "allauth",  # allauth
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.kakao",
    "allauth.socialaccount.providers.naver",
    "drf_spectacular",  # swagger
    "storages",  # s3
    "django_filters",  # filtering
    "django_seed",  # seed
    "celery",
    "django_celery_beat",
    "django_celery_results",
    "rangefilter",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = [
    *DJANGO_APPS,
    *THIRD_PARTY_APPS,
    *LOCAL_APPS,
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",  # allauth
    "repo.common.middleware.performance.PerformanceMiddleware",
]

# jwt 권한 인증 관련
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "repo.common.exception.handler.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# 로깅 설정
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "{message}",
            "style": "{",
        },
        "verbose": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{asctime}][{levelname}]=>{message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "exclude_debug_toolbar": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda log: "/__debug__/" not in log.getMessage(),
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "filters": ["require_debug_true"],
            "formatter": "server",
        },
        "performance_console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "filters": ["require_debug_true"],
            "formatter": "verbose",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "app.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "filters": ["require_debug_false"],
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "filters": ["exclude_debug_toolbar"],
            "propagate": False,
        },
        "performance": {
            "handlers": ["performance_console"],
            "level": "INFO",
            "filters": ["exclude_debug_toolbar"],
            "propagate": False,
        },
        "redis.server": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "filters": ["exclude_debug_toolbar"],
            "propagate": False,
        },
    },
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = False

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SITE_ID = 1
ROOT_URLCONF = "config.urls"

from .settings_modules.auth import *  # noqa: E402
from .settings_modules.cors import *  # noqa: E402
from .settings_modules.jwt import *  # noqa: E402
from .settings_modules.redis import *  # noqa: E402
from .settings_modules.social_auth import *  # noqa: E402
from .settings_modules.spectacular import *  # noqa: E402
