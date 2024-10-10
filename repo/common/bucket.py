import uuid
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
    from repo.profiles.models import CustomUser

    ext = filename.split('.')[-1]  # 파일 확장자

    if isinstance(instance, CustomUser):
        return f'profile/{instance.id}/{uuid.uuid4()}.{ext}'

    # 게시글 이미지
    if instance.post:
        return f'post/{instance.post.user.id}/{instance.post.id}/{uuid.uuid4()}.{ext}'

    # 시음 기록 이미지
    if instance.tasted_record:
        return f'tasted_record/{instance.tasted_record.user.id}/{instance.tasted_record.id}/{uuid.uuid4()}.{ext}'

    # 기본 경로 (이외 다른 경우)
    return f'others/{uuid.uuid4()}.{ext}'
