import uuid
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
