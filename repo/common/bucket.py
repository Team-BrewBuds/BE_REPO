import uuid

import boto3
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage, S3StaticStorage


# 장고 MEDIA 파일을 다루는 각종 설정을 커스텀할 수 있습니다.
#  - "media" 폴더에 저장되도록 location 설정을 해줍니다.
#  - "public-read" 권한으로 업로드되도록 default_acl 설정을 해줍니다.
class AwsMediaStorage(S3Boto3Storage):
    location = "media"
    default_acl = "public-read"


# 장고 STATIC 파일을 다루는 각종 설정을 커스텀할 수 있습니다.
#  - "static" 폴더에 저장되도록 location 설정을 해줍니다.
#  - "public-read" 권한으로 업로드되도록 default_acl 설정을 해줍니다.
class AwsStaticStorage(S3StaticStorage):
    location = "static"
    default_acl = "public-read"


def photo_upload_to(instance, filename):
    """
    이미지 저장 경로 결정 함수
    Args:
        instance: 관련 모델 인스턴스
        filename: 업로드 파일명

    Returns:
        str: 저장 경로
    """

    ext = filename.split(".")[-1]  # 파일 확장자
    unique_id = uuid.uuid4()

    return f"others/{unique_id}.{ext}"


def delete_photo_from_s3(photo_url: str) -> None:
    """
    S3에서 이미지 삭제 함수
    Args:
        photo_url: 삭제할 이미지 URL
    """

    s3 = boto3.client("s3", aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    s3_key = f"{AwsMediaStorage.location}/{photo_url.name}"

    try:
        s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=s3_key)
    except Exception as e:
        print(f"Failed to delete {s3_key} from S3: {e}")
    return None
