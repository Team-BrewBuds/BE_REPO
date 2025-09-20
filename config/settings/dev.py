import pymysql

from ._base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]
WSGI_APPLICATION = "config.wsgi.dev.application"
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1"]  # django debug toolbar 사용 시 필요


pymysql.install_as_MySQLdb()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env.str("LOCAL_MYSQL_DATABASE"),
        "USER": env.str("LOCAL_MYSQL_USER"),
        "PASSWORD": env.str("LOCAL_MYSQL_PASSWORD"),
        "HOST": env.str("LOCAL_MYSQL_HOST", "localhost"),
        "PORT": env.int("LOCAL_MYSQL_PORT", 3306),
    }
}

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
# FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024  # 5MB

STATIC_ROOT = "/home/app/web/static/"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# FCM
FCM_SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "secrets", "brew-buds-fcm-account.json")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console_simple": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[{server_time}] {message}",
            "style": "{",
        },
        "console_detailed": {
            "format": "[{asctime}] {name} [{levelname}] {message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
        "console_error": {
            "format": "[{asctime}] {name} [{levelname}] {pathname}:{lineno} in {funcName}\n{message}",
            "style": "{",
            "datefmt": "%H:%M:%S",
        },
    },
    "filters": {
        "exclude_debug_toolbar": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda log: "/__debug__/" not in log.getMessage(),
        },
        "exclude_error_and_above": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda log: log.levelno < 40,  # ERROR(40) 미만만 통과
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console_simple",
            "filters": ["exclude_debug_toolbar"],
        },
        "console_debug": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "console_detailed",
            "filters": ["exclude_debug_toolbar"],
        },
        "console_exclude_error_and_above": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "console_detailed",
            "filters": ["exclude_debug_toolbar", "exclude_error_and_above"],
        },
        "console_error": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "console_error",
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console_error"],
            "level": "ERROR",
            "propagate": False,
        },
        "repo": {
            "handlers": ["console_exclude_error_and_above", "console_error"],
            "level": "DEBUG",
            "propagate": False,
        },
        "performance": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
