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
