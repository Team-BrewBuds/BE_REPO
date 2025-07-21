import random
from itertools import chain

from django.core.cache import cache

from repo.common.view_tracker import RedisViewTracker
from repo.records.posts.services import PostService, get_post_service
from repo.records.tasted_record.services import (
    TastedRecordService,
    get_tasted_record_service,
)
from repo.records.views import FeedSerializer


def get_feed_service():
    post_service = get_post_service()
    tasted_record_service = get_tasted_record_service()
    return FeedService(post_service, tasted_record_service)


class FeedService:
    """피드 관련 비즈니스 로직을 처리하는 서비스"""

    def __init__(self, post_service: PostService, tasted_record_service: TastedRecordService):
        self.post_service = post_service
        self.tasted_record_service = tasted_record_service
        self.tracker = RedisViewTracker()

    def get_feed(self, request, user):
        """
        팔로우여부와 상관없이 모든 시음기록과 게시글 조회

        - 비공개 시음기록과 최근 조회한 기록은 제외
        - 차단한 사용자의 컨텐츠 제외
        - 결과는 최신순으로 정렬
        - following + common 두개의 api를 대체 가능
        """

        tasted_records = self.tasted_record_service.get_record_list_v2(user, request=request)
        posts = self.post_service.get_record_list_v2(user, request=request)

        combined_data = list(chain(tasted_records, posts))
        combined_data.sort(key=lambda x: x.created_at, reverse=True)  # 최신순
        return combined_data

    def get_following_feed(self, request, user):
        """
        팔로잉 중인 사용자들의 게시글, 시음기록 피드를 반환합니다.

        - 비공개 시음기록과 최근 조회한 기록은 제외
        - 결과는 최신순으로 정렬

        Args:
            request: HTTP 요청 객체
            user: 사용자 객체

        Returns:
            list: 시음기록과 게시글이 최신순으로 정렬된 피드 리스트
        """

        # 1. 팔로우한 유저의 시음기록, 게시글
        following_tasted_records = self.tasted_record_service.get_feed_by_follow_relation(user, follow=True)
        following_posts = self.post_service.get_feed_by_follow_relation(user, follow=True)

        # 2. 조회하지 않은 시음기록, 게시글
        not_viewed_tasted_records = self.tracker.filter_not_viewed_contents(request, "tasted_record", following_tasted_records)
        not_viewed_posts = self.tracker.filter_not_viewed_contents(request, "post", following_posts)

        # 3. 1+2 최신순으로 정렬
        combined_data = list(chain(not_viewed_tasted_records, not_viewed_posts))
        combined_data.sort(key=lambda x: x.created_at, reverse=True)
        return combined_data

    def get_common_feed(self, request, user):
        """
        일반 피드를 반환합니다.

        - 팔로잉하지 않은 사용자들의 공개 시음기록과 게시글 포함
        - 차단한 사용자의 컨텐츠 제외
        - 최근 조회한 기록 제외
        - 최신순으로 정렬

        Args:
            request: HTTP 요청 객체
            user: 사용자 객체

        Returns:
            list: 시음기록과 게시글이 최신순으로 정렬된 피드 리스트
        """

        # 1. 팔로우하지 않고 차단하지 않은 유저들의 시음기록, 게시글
        common_tasted_records = self.tasted_record_service.get_feed_by_follow_relation(user, False)
        common_posts = self.post_service.get_feed_by_follow_relation(user, False)

        # 2. 조회하지 않은 시음기록, 게시글
        not_viewed_tasted_records = self.tracker.filter_not_viewed_contents(request, "tasted_record", common_tasted_records)
        not_viewed_posts = self.tracker.filter_not_viewed_contents(request, "post", common_posts)

        # 3. 1 + 2
        combined_data = list(chain(not_viewed_tasted_records, not_viewed_posts))

        # 4. 최신순으로 정렬
        combined_data.sort(key=lambda x: x.created_at, reverse=True)

        return combined_data

    def get_refresh_feed(self, user):
        """
        새로고침용 랜덤 피드를 반환합니다.

        - 모든 공개 시음기록과 게시글 포함
        - 차단한 사용자의 컨텐츠 제외
        - 랜덤 순서로 정렬

        Args:
            user: 사용자 객체

        Returns:
            list: 시음기록과 게시글이 랜덤으로 정렬된 피드 리스트
        """
        tasted_records = self.tasted_record_service.get_refresh_feed(user)
        posts = self.post_service.get_refresh_feed(user)

        combined_data = list(chain(tasted_records, posts))

        random.shuffle(combined_data)
        return combined_data

    def get_anonymous_feed(self):
        """
        비로그인 사용자를 위한 통합 피드를 반환합니다.

        - 공개 시음기록과 모든 게시글 포함
        - 최신순 정렬

        Returns:
            list: 시음기록과 게시글이 랜덤으로 정렬된 피드 리스트
        """
        cache_key = "anonymous_feed"
        feeds = cache.get(cache_key)

        if feeds is None:
            tasted_records = self.tasted_record_service.get_base_record_list_queryset()
            posts = self.post_service.get_base_record_list_queryset()

            combined_data = list(chain(tasted_records, posts))
            combined_data.sort(key=lambda x: x.created_at, reverse=True)
            feeds = FeedSerializer(combined_data, many=True).data
            cache.set(cache_key, feeds, timeout=60 * 5)

        return feeds
