import pymysql

from ._base import *

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = False  # 수정
ALLOWED_HOSTS = [env.str("DOMAIN"), env.str("SERVER_HOST_NAME")]
WSGI_APPLICATION = "config.wsgi.prod.application"
INSTALLED_APPS += []

CSRF_TRUSTED_ORIGINS = [f"https://{env.str('DOMAIN')}"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True

pymysql.install_as_MySQLdb()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env.str("PROD_MYSQL_DATABASE"),
        "USER": env.str("PROD_MYSQL_USER"),
        "PASSWORD": env.str("PROD_MYSQL_PASSWORD"),
        "HOST": env.str("PROD_MYSQL_HOST"),
        "PORT": env.int("PROD_MYSQL_PORT"),
    }
}

# AWS
AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY_ID", default="")
AWS_S3_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_ACCESS_KEY", default="")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="ap-northeast-2")
AWS_S3_CUSTOM_DOMAIN = "%s.s3.%s.amazonaws.com" % (AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME)
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"

STATIC_ROOT = "/home/app/web/static"
STORAGES = {
    "default": {
        "BACKEND": "repo.common.bucket.AwsMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")

# FCM
FCM_SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, "secrets", "brew-buds-fcm-account.json")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "production_detailed": {
            "format": "[{asctime}] {name} [{levelname}] {process:d} {thread:d} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "exception_detailed": {
            "format": "[{asctime}] {name} [{levelname}] {pathname}:{lineno} in {funcName}\n{message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "filters": {
        "exclude_sensitive_data": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda log: not any(word in log.getMessage().lower() for word in ["password", "token", "secret", "key"]),
        },
        "exclude_error_and_above": {
            "()": "django.utils.log.CallbackFilter",
            "callback": lambda log: log.levelno < 40,  # ERROR(40) 미만만 통과
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console_critical": {
            "level": "CRITICAL",
            "class": "logging.StreamHandler",
            "formatter": "production_detailed",
            "filters": ["exclude_sensitive_data"],
        },
        "file_app": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "production_app.log",
            "maxBytes": 1024 * 1024 * 20,  # 20 MB
            "backupCount": 10,
            "formatter": "production_detailed",
            "filters": ["exclude_sensitive_data", "exclude_error_and_above"],
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "production_error.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 10,
            "formatter": "exception_detailed",
            "filters": ["exclude_sensitive_data"],
        },
        "file_critical": {
            "level": "CRITICAL",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "production_critical.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 15,
            "formatter": "exception_detailed",
        },
        "file_security": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "production_security.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 20,
            "formatter": "production_detailed",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file_app"],
            "level": "INFO",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["file_app"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error", "console_critical"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["file_security", "file_critical"],
            "level": "WARNING",
            "propagate": False,
        },
        "repo": {
            "handlers": ["file_app", "file_error"],
            "level": "INFO",
            "propagate": False,
        },
        "performance": {
            "handlers": ["file_app"],
            "level": "INFO",
            "propagate": False,
        },
        "": {
            "handlers": ["file_app"],
            "level": "WARNING",
        },
    },
}

from .settings_modules.sentry import *  # noqa: E402
