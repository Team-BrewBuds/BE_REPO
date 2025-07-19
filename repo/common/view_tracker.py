import logging

from django.core.cache import cache

from repo.common.exception.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)


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
