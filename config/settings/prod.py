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

from .settings_modules.sentry import *  # noqa: E402
