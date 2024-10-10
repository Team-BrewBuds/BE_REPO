import pymysql

from ._base import *

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = False  # 수정
ALLOWED_HOSTS = [env.str("SERVER_HOST_NAME")]  # 추후 배포할 호스트 주소 입력 예정
WSGI_APPLICATION = "config.wsgi.prod.application"  # 수정
INSTALLED_APPS += []

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
