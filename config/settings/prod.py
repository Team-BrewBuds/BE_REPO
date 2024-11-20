import pymysql

from ._base import *

SECRET_KEY = env.str("SECRET_KEY")

DEBUG = False  # 수정
ALLOWED_HOSTS = [env.str("SERVER_HOST_NAME")]
WSGI_APPLICATION = "config.wsgi.prod.application"
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

AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ACCESS_KEY_ID = env.str("AWS_S3_ACCESS_KEY_ID", default="")
AWS_S3_SECRET_ACCESS_KEY = env.str("AWS_S3_SECRET_ACCESS_KEY", default="")
AWS_S3_REGION_NAME = env.str("AWS_S3_REGION_NAME", default="ap-northeast-2")
AWS_S3_CUSTOM_DOMAIN = "%s.s3.%s.amazonaws.com" % (AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME)
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"

STORAGES = {
    "default": {
        "BACKEND": "repo.common.bucket.AwsMediaStorage",
    },
    "staticfiles": {
        "BACKEND": "repo.common.bucket.AwsStaticStorage",
    },
}

AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY")
