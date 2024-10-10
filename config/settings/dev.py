import pymysql
from ._base import *


DEBUG = True
ALLOWED_HOSTS = ['*']  # 모든 호스트 허용
WSGI_APPLICATION = 'config.wsgi.dev.application'  # 수정
INSTALLED_APPS += []

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
