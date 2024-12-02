from datetime import timedelta
from itertools import chain
from typing import Optional

from django.db import transaction
from django.db.models import BooleanField, Count, Exists, Prefetch, Q, QuerySet, Value
from django.utils import timezone

from repo.common.view_counter import get_not_viewed_contents
from repo.interactions.like.services import LikeService
from repo.interactions.note.services import NoteService
from repo.interactions.relationship.services import RelationshipService
from repo.profiles.models import CustomUser
from repo.records.base import BaseRecordService
from repo.records.models import Photo, Post, TastedRecord


def get_post_service():
    relationship_service = RelationshipService()
    like_service = LikeService("post")
    note_service = NoteService()
    return PostService(relationship_service, like_service, note_service)


class PostService(BaseRecordService):
    """게시글 관련 비즈니스 로직을 처리하는 서비스"""

    def __init__(self, relationship_service, like_service, note_service):
        super().__init__(relationship_service, like_service, note_service)

    def get_record_detail(self, pk: int) -> Post:
        """게시글 상세 조회"""
        return (
            Post.objects.filter(pk=pk)
            .select_related("author")
            .prefetch_related(
                Prefetch("tasted_records", queryset=TastedRecord.objects.select_related("bean", "taste_review")),
                Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
            )
            .first()
        )

    def get_user_records(self, user_id, **kwargs) -> QuerySet[Post]:
        """유저가 작성한 게시글 조회"""
        user = CustomUser.objects.get(id=user_id)
        subject = kwargs.get("subject", None)

        subject_filter = Q(subject=subject) if subject != "all" else Q()

        posts = (
            user.post_set.filter(subject_filter)
            .select_related("author")
            .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .order_by("-id")
        )
        return posts

    def get_record_list(self, user: CustomUser, **kwargs) -> QuerySet[Post]:
        """홈 게시글 리스트 조회"""
        subject = kwargs.get("subject", None)
        request = kwargs.get("request", None)

        following_users = self.relationship_service.get_following_user_list(user.id)

        add_filter = {"author__in": following_users}
        following_posts = self.get_feed_queryset(user, add_filter, None, subject)
        unfollowing_posts = self.get_unfollowing_feed(user)

        posts = list(chain(following_posts, unfollowing_posts))

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

    def get_top_subject_weekly_posts(self, user: Optional[CustomUser], subject: str) -> QuerySet[Post]:
        """특정 주제의 게시글 중 일주일 안에 조회수 상위 60개를 가져오는 함수"""
        top_posts_base = self._get_base_weekly_posts()

        if subject:
            top_posts_base = top_posts_base.filter(subject=subject)

        if user is None:
            return self._get_anonymous_top_posts(top_posts_base)

        return self._get_authenticated_top_posts(user, top_posts_base)

    def _get_base_weekly_posts(self) -> QuerySet[Post]:
        """일주일 이내의 기본 게시글 쿼리셋을 반환"""
        time_threshold = timezone.now() - timedelta(days=7)
        print(
            Post.objects.filter(created_at__gte=time_threshold).annotate(
                likes=Count("like_cnt", distinct=True),
                comments=Count("comment", distinct=True),
            )
        )
        return Post.objects.filter(created_at__gte=time_threshold).annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
        )

    def _get_anonymous_top_posts(self, queryset: QuerySet[Post]) -> QuerySet[Post]:
        """비로그인 사용자를 위한 상위 게시글 반환"""
        return queryset.order_by("-view_cnt")[:60]

    def _get_authenticated_top_posts(self, user: CustomUser, queryset: QuerySet[Post]) -> QuerySet[Post]:
        """로그인 사용자를 위한 상위 게시글 반환"""
        block_users = self.relationship_service.get_unique_blocked_user_list(user.id)

        return (
            queryset.exclude(author__in=block_users)
            .annotate(
                is_user_liked=Exists(self.like_service.get_like_subquery_for_post(user)),
            )
            .order_by("-view_cnt")[:60]
        )

    def _set_post_relations(self, post: Post, data: dict):
        """게시글 관계 데이터 설정"""
        if tasted_records := data.get("tasted_records"):
            post.tasted_records.set(tasted_records)
        if photos := data.get("photos"):
            post.photo_set.set(photos)

    ## 피드 조회 관련 메서드

    def get_base_record_list_queryset(self, user: Optional[CustomUser] = None):
        """공통적으로 사용하는 기본 쿼리셋 생성"""
        base_queryset = (
            Post.objects.select_related("author")
            .prefetch_related("tasted_records", "comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .annotate(
                likes=Count("like_cnt", distinct=True),
                comments=Count("comment", distinct=True),
            )
        )
        if user:
            base_queryset = base_queryset.annotate(
                is_user_liked=Exists(self.like_service.get_like_subquery_for_post(user)),
                is_user_noted=Exists(self.note_service.get_note_subquery_for_post(user)),
            )
        return base_queryset

    def get_feed_queryset(self, user, add_filter=None, exclude_filter=None, subject=None):
        """
        게시글 피드를 위한 필터링된 쿼리셋 생성

        Args:
            user: 사용자 객체
            add_filter: 추가할 필터 조건 (dict)
            exclude_filter: 제외할 필터 조건 (dict)
            subject: 게시글 주제

        Returns:
            QuerySet: 필터링된 게시글 쿼리셋
        """

        base_queryset = self.get_base_record_list_queryset(user)

        filters = Q(**add_filter) if add_filter else Q()
        excludes = Q(**exclude_filter) if exclude_filter else Q()

        if user:  # 기본적으로 차단한 사용자는 제외
            block_users = self.relationship_service.get_unique_blocked_user_list(user.id)
            filters &= ~Q(author__in=block_users)

        if subject:
            filters &= Q(subject=subject)

        return base_queryset.filter(filters).exclude(excludes)

    def get_following_feed(self, user: CustomUser) -> QuerySet[Post]:
        following_users = self.relationship_service.get_following_user_list(user.id)

        add_filter = {"author__in": following_users}

        return self.get_feed_queryset(user, add_filter, None, None)

    # home following feed
    def get_following_feed_and_gte_one_hour(self, user: CustomUser) -> QuerySet[Post]:
        one_hour_ago = timezone.now() - timedelta(hours=1)
        add_filter = {"created_at__gte": one_hour_ago}

        following_feed = self.get_following_feed(user)

        return following_feed.filter(add_filter)

    # home common feed
    def get_unfollowing_feed(self, user: CustomUser) -> QuerySet[Post]:
        following_users = self.relationship_service.get_following_user_list(user.id)

        exclude_filter = {"author__in": following_users}

        return self.get_feed_queryset(user, None, exclude_filter, None)

    # home refresh feed
    def get_refresh_feed(self, user: CustomUser) -> QuerySet[Post]:
        return self.get_feed_queryset(user, None, None, None)

    # 비로그인 사용자를 위한 게시글 피드
    def get_record_list_for_anonymous(self) -> QuerySet[Post]:
        """비로그인 사용자 게시글 피드 조회"""
        return (
            Post.objects.select_related("author")
            .prefetch_related("tasted_records", "comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .annotate(
                likes=Count("like_cnt", distinct=True),
                comments=Count("comment", distinct=True),
                is_user_liked=Value(False, output_field=BooleanField()),  # False 고정
                is_user_noted=Value(False, output_field=BooleanField()),  # False 고정
            )
            .order_by("?")
        )
