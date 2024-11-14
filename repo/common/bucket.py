import uuid

import boto3
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage

from repo.profiles.models import CustomUser

DEBUG = settings.DEBUG

if not DEBUG:
    AWS_S3_ACCESS_KEY_ID = settings.AWS_S3_ACCESS_KEY_ID
    AWS_S3_SECRET_ACCESS_KEY = settings.AWS_S3_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME


# 장고 STATIC 파일을 다루는 각종 설정을 커스텀할 수 있습니다.
#  - "static" 폴더에 저장되도록 location 설정을 해줍니다.
#  - "public-read" 권한으로 업로드되도록 default_acl 설정을 해줍니다.
class AwsStaticStorage(S3StaticStorage):
    location = "static"
    default_acl = "public-read"


# 장고 MEDIA 파일을 다루는 각종 설정을 커스텀할 수 있습니다.
#  - "media" 폴더에 저장되도록 location 설정을 해줍니다.
#  - "public-read" 권한으로 업로드되도록 default_acl 설정을 해줍니다.
class AwsMediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = "public-read"

    def _save(self, name, content):
        """
        장고 MEDIA 파일을 S3에 업로드하는 함수
        Args:
            name: 업로드할 파일 이름
            content: 업로드할 파일 내용
        Returns:
            str: 업로드된 파일 이름
        """

        s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY,
        )

        content.seek(0)

        file_name = name.split("/")[-1]  # 파일명

        try:
            s3.put_object(
                Bucket=AWS_STORAGE_BUCKET_NAME,
                Key=f"{self.location}/{name}",
                Body=content,
                ContentType=content.content_type,
                Metadata={"is-representative": str(file_name.startswith("main_")).lower()},  # 'true' or 'false'
                ACL="public-read",
            )
            return name
        except Exception as e:
            raise e


def create_unique_filename(filename, is_main=False):
    """
    고유한 이미지 이름 생성 함수
    Args:

    Returns:
        str: 고유한 이미지 이름
    """
    ext = filename.split(".")[-1]  # 파일 확장자
    unique_id = uuid.uuid4()

    if is_main:
        return f"main_{unique_id}.{ext}"
    return f"{unique_id}.{ext}"


def delete_photo(photo_url: str) -> None:
    """
    S3에서 이미지 삭제 함수
    Args:
        photo_url: 삭제할 이미지 URL
    """
    try:
        s3 = boto3.client("s3", aws_access_key_id=AWS_S3_ACCESS_KEY_ID, aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY)
        s3_key = f"{AwsMediaStorage.location}/{photo_url.name}"

        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except Exception as e:
        raise e
    return None


def delete_photos(object) -> None:
    """
    S3에서 여러 이미지를 한 번에 삭제하는 함수
    Args:
        object: 삭제할 이미지를 포함하는 객체
    """
    if not object.photo_set.exists():
        return None

    photos = object.photo_set.all()
    try:
        if DEBUG:
            for photo in photos:
                photo.photo_url.delete()
            photos.delete()
        else:
            s3 = boto3.client("s3", aws_access_key_id=AWS_S3_ACCESS_KEY_ID, aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY)

            # S3에서 삭제할 객체 목록 생성
            objects = [{"Key": f"{AwsMediaStorage.location}/{photo.photo_url.name}"} for photo in photos]

            objects_to_delete = {
                "Objects": objects,
                "Quiet": True,  # 삭제 결과 메시지를 간소화
            }

            # 일괄 삭제 요청
            s3.delete_objects(Bucket=AWS_STORAGE_BUCKET_NAME, Delete=objects_to_delete)
            photos.delete()

    except Exception as e:
        raise e
    return None


def delete_profile_photo(user: CustomUser) -> None:
    """
    프로필 이미지 삭제 함수
    Args:
        user: 프로필 이미지를 삭제할 유저
    """
    if not user.profile_image:
        return None

    try:
        if DEBUG:
            user.profile_image.delete()
        else:
            delete_photo(user.profile_image)
            user.profile_image = None
            user.save(update_fields=["profile_image"])
    except Exception as e:
        raise e
    return None
