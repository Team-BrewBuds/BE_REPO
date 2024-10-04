import json
from django.utils import timezone
from datetime import timedelta
from rest_framework.response import Response


def is_viewed(request, cookie_name, content_id): 
    """
    쿠키에 저장된 조회한 게시글 목록에 포함되어 있는지 확인하는 헬퍼 함수
    Args:
        request: request 객체
        cookie_name: 쿠키 이름
        content_id: 조회한 게시글 ID
    Returns:
        bool: 조회한 게시글 목록에 포함되어 있는지 여부
    담당자: hwstar1204
    """
    try:
        # 쿠키에서 조회한 게시글 목록 가져오기 (JSON 형식 사용)
        viewed_contents = request.COOKIES.get(cookie_name)

        if viewed_contents:
            viewed_contents = json.loads(viewed_contents)
            if str(content_id) in viewed_contents:
                return True
    except (json.JSONDecodeError, TypeError):
        # 쿠키 값이 잘못된 경우 False 반환
        return False

    return False