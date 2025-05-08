import logging
import random
from datetime import timedelta
from typing import Optional

from django.core.cache import cache
from django.db import transaction
from django.db.models import BooleanField, Exists, Prefetch, Q, QuerySet, Value
from django.utils import timezone

from repo.beans.services import BeanService
from repo.common.view_counter import get_not_viewed_contents
from repo.interactions.like.services import LikeService
from repo.interactions.note.services import NoteService
from repo.interactions.relationship.services import RelationshipService
from repo.profiles.models import CustomUser
from repo.profiles.services import UserService
from repo.records.base import BaseRecordService
from repo.records.models import BeanTasteReview, Photo, TastedRecord
from repo.records.tasted_record.serializers import TastedRecordListSerializer

redis_logger = logging.getLogger("redis.server")


def get_tasted_record_service():
    relationship_service = RelationshipService()
    like_service = LikeService("tasted_record")
    note_service = NoteService()
    return TastedRecordService(relationship_service, like_service, note_service)


class TastedRecordService(BaseRecordService):

    def __init__(self, relationship_service, like_service, note_service):
        super().__init__(relationship_service, like_service, note_service)
        self.bean_service = BeanService()
        self.user_service = UserService()

    def get_record_detail(self, pk: int) -> TastedRecord:
        """시음기록 상세 조회"""
        return TastedRecord.objects.select_related("author", "bean", "taste_review").prefetch_related("photo_set").get(pk=pk)

    def get_user_records(self, user_id: int, **kwargs) -> QuerySet[TastedRecord]:
        """유저가 작성한 시음기록 조회"""
        user = self.user_service.get_user_by_id(user_id)

        return (
            TastedRecord.objects.filter(author=user)
            .select_related("bean", "taste_review")
            .prefetch_related(
                Prefetch(
                    "photo_set",
                    queryset=Photo.objects.only("photo_url", "tasted_record_id"),
                    to_attr="tasted_record_photos",
                )
            )
            .only("id", "bean__name", "taste_review__star", "created_at", "likes")
        )

    def get_record_list(self, user: CustomUser, **kwargs) -> QuerySet[TastedRecord]:
        """홈 시음기록 리스트 조회"""
        request = kwargs.get("request", None)

        following_tasted_records = self.annotate_user_interactions(self.get_feed_by_follow_relation(user, True), user).order_by("-id")
        unfollowing_tasted_records = self.annotate_user_interactions(self.get_feed_by_follow_relation(user, False), user).order_by("-id")

        tasted_records = following_tasted_records.union(unfollowing_tasted_records, all=True)

        if request:
            tasted_records = get_not_viewed_contents(request, tasted_records, "tasted_record_viewed")

        return tasted_records

    @transaction.atomic
    def create_record(self, user: CustomUser, validated_data: dict) -> TastedRecord:
        """시음기록 생성"""

        bean = self.bean_service.create(validated_data["bean"])

        taste_review = BeanTasteReview.objects.create(**validated_data["taste_review"])

        tasted_record = TastedRecord.objects.create(
            author=user,
            bean=bean,
            taste_review=taste_review,
            content=validated_data["content"],
        )

        photos = validated_data.get("photos", [])
        tasted_record.photo_set.set(photos)

        return tasted_record

    @transaction.atomic
    def update_record(self, tasted_record: TastedRecord, validated_data: dict) -> TastedRecord:
        """시음기록 업데이트"""

        for attr, value in validated_data.items():
            if attr not in ["bean", "taste_review", "photos"]:  # 원두 데이터는 수정 불가
                setattr(tasted_record, attr, value)

        self._set_tasted_record_relations(tasted_record, validated_data)

        tasted_record.save()
        return tasted_record

    @transaction.atomic
    def delete_record(self, tasted_record: TastedRecord):
        """시음기록 삭제"""
        tasted_record.delete()

    def _set_tasted_record_relations(self, tasted_record: TastedRecord, data: dict):
        """시음기록 관계 데이터 설정"""

        if taste_review_data := data.get("taste_review"):
            taste_review, _ = BeanTasteReview.objects.update_or_create(
                id=tasted_record.taste_review_id,
                defaults=taste_review_data,
            )
            tasted_record.taste_review = taste_review

        if photos := data.get("photos"):
            tasted_record.photo_set.set(photos)

    # 피드 조회 관련 메서드
    @staticmethod
    def get_base_record_list_queryset() -> QuerySet[TastedRecord]:
        """공통적으로 사용하는 기본 시음기록 리스트 쿼리셋 생성"""
        return (
            TastedRecord.objects.select_related(
                "author",
                "bean",
                "taste_review",
            )
            .prefetch_related(
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
        )

    def get_feed_queryset(self, user: CustomUser, filters: Optional[Q] = None) -> QuerySet[TastedRecord]:
        """
        시음기록 피드 쿼리셋 조회

        Args:
            user: 사용자 객체
            add_filter: 추가할 필터 조건 (Q)

        Returns:
            QuerySet: 필터링된 시음기록 쿼리셋
        """
        base_queryset = self.get_base_record_list_queryset().annotate(
            is_user_liked=Exists(self.like_service.get_like_subquery_for_tasted_record(user)),
            is_user_noted=Exists(self.note_service.get_note_subquery_for_tasted_record(user)),
        )

        block_users = self.relationship_service.get_unique_blocked_user_list(user.id)

        filters = filters if filters else Q()
        filters &= ~Q(author__in=block_users)  # 차단한 유저 필터링
        filters &= Q(is_private=False)  # 비공개 시음기록 필터링

        return base_queryset.filter(filters)

    def get_feed_by_follow_relation(self, user: CustomUser, follow: bool) -> QuerySet[TastedRecord]:
        """팔로잉 관계에 따른 피드 조회"""
        following_users = self.relationship_service.get_following_user_list(user.id)

        filters = Q(author__in=following_users) if follow else ~Q(author__in=following_users)

        return self.get_feed_queryset(user, filters).annotate(is_user_following=Value(follow, output_field=BooleanField()))

    # home following feed
    def get_following_feed_and_gte_one_hour(self, user: CustomUser) -> QuerySet[TastedRecord]:
        """팔로잉한 사용자의 최근 1시간 이내 피드 조회"""
        following_feed = self.get_feed_by_follow_relation(user, True)

        one_hour_ago = timezone.now() - timedelta(hours=1)
        add_filter = Q(created_at__gte=one_hour_ago)

        return following_feed.filter(add_filter)

    # home refresh feed
    def get_refresh_feed(self, user: CustomUser) -> QuerySet[TastedRecord]:
        """새로고침용 피드 조회"""
        return self.get_feed_queryset(user).annotate(
            is_user_following=Exists(self.relationship_service.get_following_subquery_for_record(user))
        )

    # 비로그인 사용자 시음기록 피드 조회
    def get_record_list_for_anonymous(self) -> QuerySet[TastedRecord]:
        """비로그인 사용자 시음기록 피드 조회"""
        cache_key = "anonymous_tasted_record_list"
        records = cache.get(cache_key)

        if records is None:
            base_records_queryset = self.get_base_record_list_queryset()
            public_records_queryset = base_records_queryset.filter(is_private=False)
            records = TastedRecordListSerializer(public_records_queryset, many=True).data
            cache.set(cache_key, records, timeout=60 * 5)

        random.shuffle(records)
        return records
