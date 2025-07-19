import json
import logging

from django.core.cache import cache

from repo.common.exception.exceptions import UnauthorizedException

COOKIE_EXP_MIN = 30

logger = logging.getLogger(__name__)


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


def get_not_viewed_contents(request, queryset, cookie_name):
    """
    사용자가 아직 조회하지 않은 데이터만 필터링하여 반환합니다.

    Args:
        request: HTTP 요청 객체
        queryset: 필터링할 쿼리셋
        cookie_name: 조회 여부를 확인할 쿠키 이름

    Returns:
        list: 조회하지 않은 데이터 리스트
    """
    return [content for content in queryset if not is_viewed(request, cookie_name=cookie_name, content_id=content.id)]


class RedisViewTracker:
    """
    조회수 추적을 위한 Redis 클라이언트
    """

    REDIS_VIEW_EXP_SEC = 60 * 30  # 30분
    MAX_VIEWED_ITEMS = 100

    def get_cache_key(self, request, content_type) -> str:
        """Redis 키 생성"""
        if not request.user.is_authenticated:
            raise UnauthorizedException("인증된 사용자만 조회할 수 있습니다.")
        return f"user:{request.user.id}:viewed:{content_type}"

    def track_view(self, request, content_type, content_id) -> bool:
        """조회 여부 추가 및 조회 이력 관리"""
        try:
            cache_key = self.get_cache_key(request, content_type)
            viewed_list = cache.get(cache_key, [])
            if str(content_id) in viewed_list:
                return False

            viewed_list.append(str(content_id))
            if len(viewed_list) > self.MAX_VIEWED_ITEMS:  # 최대 개수 초과 시 오래된 항목 제거
                viewed_list.pop(0)
            cache.set(cache_key, viewed_list, timeout=self.REDIS_VIEW_EXP_SEC)
            return True
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.warning(f"조회 추적 실패: {str(e)}")
            return False

    def is_viewed(self, request, content_type, content_id) -> bool:
        """조회 여부 확인"""
        try:
            cache_key = self.get_cache_key(request, content_type)
            viewed_list = cache.get(cache_key, [])
            return str(content_id) in viewed_list
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.warning(f"조회 확인 실패: {str(e)}")
            return False

    def get_user_viewed_contents(self, request, content_type) -> set[str]:
        """사용자가 조회한 콘텐츠 목록 조회"""
        try:
            cache_key = self.get_cache_key(request, content_type)
            viewed_list = cache.get(cache_key, [])
            return set(map(int, viewed_list)) if viewed_list else set()
        except UnauthorizedException:
            raise
        except Exception as e:
            logger.warning(f"조회 이력 가져오기 실패: {str(e)}")
            return set()

    def filter_not_viewed_contents(self, request, content_type, queryset) -> list:
        """사용자가 아직 조회하지 않은 데이터만 필터링하여 반환합니다."""
        viewed_contents = self.get_user_viewed_contents(request, content_type)
        return [content for content in queryset if content.id not in viewed_contents]

    def update_view_count(self, instance) -> bool:
        """조회수 업데이트"""
        instance.view_cnt += 1
        instance.save(update_fields=["view_cnt"])
        return instance
