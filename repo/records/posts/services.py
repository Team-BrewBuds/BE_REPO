import logging
import random
from datetime import timedelta
from typing import Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import BooleanField, Count, Exists, Prefetch, Q, QuerySet, Value
from django.utils import timezone
from redis.exceptions import ConnectionError

from repo.common.utils import get_last_monday
from repo.common.view_counter import get_not_viewed_contents
from repo.interactions.like.services import LikeService
from repo.interactions.note.services import NoteService
from repo.interactions.relationship.services import RelationshipService
from repo.profiles.models import CustomUser
from repo.records.base import BaseRecordService
from repo.records.models import Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.posts.tasks import cache_top_posts

redis_logger = logging.getLogger("redis.server")
cache_key = "post_list_ids"


def get_post_service():
    relationship_service = RelationshipService()
    like_service = LikeService("post")
    note_service = NoteService()
    return PostService(relationship_service, like_service, note_service)


def get_top_post_service():
    relationship_service = RelationshipService()
    like_service = LikeService("post")
    return TopPostService(relationship_service, like_service)


class PostService(BaseRecordService):
    """게시글 관련 비즈니스 로직을 처리하는 서비스"""

    def __init__(self, relationship_service, like_service, note_service):
        super().__init__(relationship_service, like_service, note_service)

    def get_record_detail(self, pk: int) -> Post:
        """게시글 상세 조회"""
        return (
            Post.objects.filter(pk=pk)
            .select_related("author")
            .prefetch_related(Prefetch("tasted_records", queryset=TastedRecord.objects.select_related("bean", "taste_review")), "photo_set")
            .first()
        )

    def get_user_records(self, user_id: int, **kwargs) -> QuerySet[Post]:
        """유저가 작성한 게시글 조회"""
        user = CustomUser.objects.get(id=user_id)
        subject = kwargs.get("subject", None)

        filters = Q(author=user)
        if subject:
            filters &= Q(subject=subject)

        posts = (
            Post.objects.filter(filters)
            .select_related("author")
            .prefetch_related("photo_set", Prefetch("tasted_records", queryset=TastedRecord.objects.prefetch_related("photo_set")))
            .order_by("-id")
        )
        return posts

    def get_record_list(self, user: CustomUser, **kwargs) -> QuerySet[Post]:
        """홈 게시글 리스트 조회"""
        request = kwargs.get("request", None)
        subject = kwargs.get("subject", None)

        filters = Q(subject=subject) if subject else Q()

        following_posts = self.annotate_user_interactions(self.get_feed_by_follow_relation(user, True).filter(filters), user).order_by(
            "-id"
        )
        unfollowing_posts = self.annotate_user_interactions(self.get_feed_by_follow_relation(user, False).filter(filters), user).order_by(
            "-id"
        )

        posts = following_posts.union(unfollowing_posts, all=True)

        if request:
            posts = get_not_viewed_contents(request, posts, "post_viewed")

        return posts

    @transaction.atomic
    def create_record(self, user: CustomUser, validated_data: dict) -> Post:
        """게시글 생성"""
        post = Post.objects.create(
            author=user,
            title=validated_data["title"],
            content=validated_data["content"],
            subject=validated_data["subject"],
            tag=validated_data.get("tag", None),
        )
        self._set_post_relations(post, validated_data)
        return post

    @transaction.atomic
    def update_record(self, post: Post, validated_data: dict) -> Post:
        """게시글 수정 및 관련 데이터 업데이트"""

        for attr, value in validated_data.items():
            if attr not in ["tasted_records", "photos"]:
                setattr(post, attr, value)

        self._set_post_relations(post, validated_data)

        post.save()
        return post

    def delete_record(self, post: Post):
        """게시글 삭제"""
        post.delete()

    def _set_post_relations(self, post: Post, data: dict):
        """게시글 관계 데이터 설정"""
        if tasted_records := data.get("tasted_records"):
            post.tasted_records.set(tasted_records)
        if photos := data.get("photos"):
            post.photo_set.set(photos)

    ## 피드 조회 관련 메서드
    @staticmethod
    def get_base_record_list_queryset() -> QuerySet[Post]:
        """공통적으로 사용하는 기본 쿼리셋 생성"""
        return (
            Post.objects.select_related("author")
            .prefetch_related(
                "tasted_records",
                "tasted_records__bean",
                "tasted_records__taste_review",
                "tasted_records__photo_set",
                "note_set",
                "photo_set",
                "comment_set",
            )
            .defer(
                "author__gender",
                "author__birth",
                "author__email",
                "author__login_type",
                "author__social_id",
                "author__password",
                "author__is_active",
                "author__is_superuser",
                "author__is_staff",
                "author__last_login",
                "author__created_at",
            )
            .order_by("-id")
        )

    def get_feed_queryset(self, user: CustomUser, add_filter: Optional[Q] = None, subject: Optional[str] = None) -> QuerySet[Post]:
        """
        게시글 피드를 위한 필터링된 쿼리셋 생성

        Args:
            user: 사용자 객체
            add_filter: 추가할 필터 조건 (Q)
            subject: 게시글 주제

        Returns:
            QuerySet: 필터링된 게시글 쿼리셋
        """
        base_queryset = self.get_base_record_list_queryset().annotate(
            is_user_liked=Exists(self.like_service.get_like_subquery_for_post(user)),
            is_user_noted=Exists(self.note_service.get_note_subquery_for_post(user)),
        )

        block_users = self.relationship_service.get_unique_blocked_user_list(user.id)

        filters = add_filter if add_filter else Q()
        filters &= ~Q(author__in=block_users)  # 차단한 유저 필터링
        filters &= Q(subject=subject) if subject else Q()  # 주제 필터링

        return base_queryset.filter(filters)

    def get_feed_by_follow_relation(self, user: CustomUser, follow: bool) -> QuerySet[Post]:
        """팔로잉 관계에 따른 피드 조회"""
        following_users = self.relationship_service.get_following_user_list(user.id)

        filters = Q(author__in=following_users) if follow else ~Q(author__in=following_users)

        return self.get_feed_queryset(user, filters, None).annotate(is_user_following=Value(follow, output_field=BooleanField()))

    # home following feed
    def get_following_feed_and_gte_one_hour(self, user: CustomUser) -> QuerySet[Post]:
        """팔로잉한 사용자의 최근 1시간 이내 피드 조회"""
        following_feed = self.get_feed_by_follow_relation(user, True)

        one_hour_ago = timezone.now() - timedelta(hours=1)
        add_filter = Q(created_at__gte=one_hour_ago)

        return following_feed.filter(add_filter)

    # home refresh feed
    def get_refresh_feed(self, user: CustomUser) -> QuerySet[Post]:
        return self.get_feed_queryset(user, None, None).annotate(
            is_user_following=Exists(self.relationship_service.get_following_subquery_for_record(user))
        )

    # 비로그인 사용자를 위한 게시글 피드
    def get_record_list_for_anonymous(self, subject: Optional[str] = None) -> list:
        """
        비로그인 사용자 게시글 피드 조회

        Args:
            subject: 게시글 주제 (선택)

        Returns:
            list: 캐시된 게시글 목록
        """
        cache_key = "anonymous_posts"
        posts = cache.get(cache_key)

        if posts is None:
            base_post_queryset = self.get_base_record_list_queryset()
            posts = PostListSerializer(base_post_queryset, many=True).data
            cache.set(cache_key, posts, timeout=60 * 5)

        if subject:
            subject_value = dict(Post.SUBJECT_TYPE_CHOICES)[subject]
            posts = [post for post in posts if post["subject"] == subject_value]

        random.shuffle(posts)
        return posts


class TopPostService:
    TOP_POSTS_LIMIT = 60  # 최대 60개 조회

    def __init__(self, relationship_service: RelationshipService, like_service: LikeService):
        self.relationship_service = relationship_service
        self.like_service = like_service

    def get_top_subject_weekly_posts(self, user: Optional[CustomUser], subject: Optional[str]) -> QuerySet[Post]:
        """특정 주제의 주간 인기 게시글 조회"""

        current = timezone.now()
        time_threshold = get_last_monday(current)

        # 기본 필터링
        base_filters = self._get_base_filters(subject, time_threshold)
        top_posts_base = self._get_base_queryset(base_filters)

        if not user or not user.is_authenticated:
            return self._get_public_posts(top_posts_base)

        return self._get_authenticated_user_posts(user, top_posts_base)

    def _get_base_filters(self, subject: Optional[str], time_threshold: timezone) -> Q:
        """기본 필터 구성"""
        filters = Q(created_at__range=(time_threshold, time_threshold + timedelta(days=7)))

        if subject:
            filters &= Q(subject=subject)
        return filters

    def _get_base_queryset(self, filters: Q) -> QuerySet[Post]:
        """기본 쿼리셋 생성"""
        return (
            Post.objects.select_related("author")
            .filter(filters)
            .annotate(
                comments=Count("comment", distinct=True),
            )
        )

    def _get_public_posts(self, queryset: QuerySet[Post]) -> QuerySet[Post]:
        """비회원용 쿼리셋"""
        return queryset.annotate(is_user_liked=Value(False, output_field=BooleanField())).order_by("-view_cnt")[: self.TOP_POSTS_LIMIT]

    def _get_authenticated_user_posts(self, user: CustomUser, queryset: QuerySet[Post]) -> QuerySet[Post]:
        """회원용 쿼리셋"""
        blocked_users = self.relationship_service.get_unique_blocked_user_list(user.id)
        like_subquery = self.like_service.get_like_subquery_for_post(user)

        return (
            queryset.exclude(author__in=blocked_users)
            .annotate(
                is_user_liked=Exists(like_subquery),
            )
            .order_by("-view_cnt")[: self.TOP_POSTS_LIMIT]
        )

    def get_top_posts(self, subject: str, user: Optional[CustomUser] = None):
        """인기 게시글 조회 (레디스 연결 실패시 직접 DB 조회)"""
        try:
            if not subject:
                subject = ""
            cache_key = f"top_posts:{subject}:weekly"
            cached_data = cache.get(cache_key)

            if not cached_data:
                cache_top_posts()  # 캐시 업데이트
                cached_data = cache.get(cache_key)

            posts = cached_data

            if not user or not user.is_authenticated:  # 비회원
                return self.get_top_posts_for_anonymous_user(posts)

            return self.get_top_posts_for_authenticated_user(user.id, posts)
        except ConnectionError as e:
            redis_logger.error(f"Redis 연결 실패 post_list_ids: {str(e)}", exc_info=True)
            return self.get_top_subject_weekly_posts(user, subject)

    def get_top_posts_for_authenticated_user(self, user_id: int, posts: list):
        # 차단한 유저 필터링
        blocked_users = self.relationship_service.get_unique_blocked_user_list(user_id)
        posts = [post for post in posts if post["author"]["id"] not in blocked_users]

        # 좋아요 여부 확인
        for post in posts:
            post["is_user_liked"] = Post.objects.filter(id=post["id"], like_cnt__id=user_id).exists()
        return posts

    def get_top_posts_for_anonymous_user(self, posts: list):
        for post in posts:
            post["is_user_liked"] = False
        return posts
