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
    unique_id = uuid.uuid4()

    if isinstance(instance, CustomUser):
        return f'profile/{unique_id}/.{ext}'

    # Post 이미지
    elif instance.post:
        author_id = instance.post.author.id
        post_id = instance.post.id
        return f'post/{author_id}/{post_id}/{unique_id}.{ext}'

    # TastedRecord 이미지
    elif instance.tasted_record:
        author_id = instance.tasted_record.author.id
        tasted_record_id = instance.tasted_record.id
        return f'tasted_record/{author_id}/{tasted_record_id}/{unique_id}.{ext}'

    # 기본 경로 (이외 다른 경우)
    return f'others/{uuid.uuid4()}.{ext}'
