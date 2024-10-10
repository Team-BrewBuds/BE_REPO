import json
from datetime import datetime, timedelta

from django.utils import timezone

COOKIE_EXP_MIN = 30


def update_view_count(request, instance, response, cookie_name, expiration_minutes=COOKIE_EXP_MIN):
    """
    쿠키를 기반으로 조회수를 업데이트하는 헬퍼 함수
    Args:
        request: request 객체
        instance: 조회수를 업데이트할 모델 객체
        response: Response 객체
        cookie_name: 쿠키 이름
        expiration_minutes: 쿠키 만료 시간 (분)
    Returns:
        tuple: 업데이트된 모델 객체와 Response 객체
    담당자: hwstar1204
    """
    update_needed = is_need_update(request, cookie_name, expiration_minutes)

    if update_needed:
        instance.view_cnt += 1
        instance.save(update_fields=["view_cnt"])

        viewed_contents = request.COOKIES.get(cookie_name)
        if viewed_contents:
            try:
                viewed_contents = json.loads(viewed_contents)
            except (json.JSONDecodeError, TypeError):
                viewed_contents = []
        else:
            viewed_contents = []

        viewed_contents.append(str(instance.id))

        response.set_cookie(cookie_name, json.dumps(viewed_contents), max_age=expiration_minutes * 60)

    return instance, response


def is_need_update(request, cookie_name, expiration_minutes=COOKIE_EXP_MIN):
    """
    쿠키를 기반으로 조회수 업데이트가 필요한지 확인하는 헬퍼 함수
    Args:
        request: request 객체
        cookie_name: 쿠키 이름
        expiration_minutes: 쿠키 만료 시간 (분)
    Returns:
        bool: 조회수 업데이트가 필요한지 여부
    담당자: hwstar1204
    """
    view_token = request.COOKIES.get(cookie_name)

    if view_token:
        last_viewed_time = datetime.strptime(view_token, "%Y-%m-%d %H:%M:%S")  # 쿠키에 저장된 시간
        time_threshold = timezone.now() - timedelta(minutes=expiration_minutes)  # 만료 시간

        if last_viewed_time < time_threshold:  # 마지막 조회 시간이 만료 시간 이전인지 확인
            return True

    else:
        return True  # 조회수 토큰이 없으면 조회수 업데이트 필요

    return False


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
