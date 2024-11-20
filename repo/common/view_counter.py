import json

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

    if is_viewed(request, cookie_name, instance.id):
        return response

    instance.view_cnt += 1
    instance.save(update_fields=["view_cnt"])

    viewed_contents = get_viewed_contents(request, cookie_name)
    viewed_contents.append(str(instance.id))

    response.set_cookie(cookie_name, json.dumps(viewed_contents), max_age=expiration_minutes * 60, httponly=True)  # 초 단위

    return response


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

    viewed_contents = get_viewed_contents(request, cookie_name)
    return str(content_id) in viewed_contents


def get_viewed_contents(request, cookie_name):
    """
    쿠키에서 조회한 게시글 목록을 가져오는 헬퍼 함수
    Args:
        request: request 객체
        cookie_name: 쿠키 이름
    Returns:
        list: 조회한 게시글 목록
    담당자: hwstar1204
    """
    viewed_contents = json.loads(request.COOKIES.get(cookie_name, "[]"))
    return viewed_contents
