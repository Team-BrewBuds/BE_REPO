from datetime import timedelta
from itertools import chain
from typing import Dict, Optional

from django.db import transaction
from django.db.models import BooleanField, Count, Exists, Prefetch, Q, QuerySet, Value
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

    def get_record_detail(self, pk):
        """시음기록 상세 조회"""
        return (
            TastedRecord.objects.select_related("author", "bean", "taste_review")
            .prefetch_related(
                Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
            )
            .get(pk=pk)
        )

    def get_user_records(self, user_id, **kwargs):
        """유저가 작성한 시음기록 조회"""
        user = self.user_service.get_user_by_id(user_id)
        return (
            user.tastedrecord_set.select_related("bean", "taste_review")
            .prefetch_related("like_cnt", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .only("id", "bean__name", "taste_review__star", "created_at", "like_cnt")
            .annotate(
                likes=Count("like_cnt", distinct=True),
            )
        )

    def get_record_list(self, user: CustomUser, **kwargs) -> QuerySet[TastedRecord]:
        """홈 시음기록 리스트 조회"""
        request = kwargs.get("request", None)

        following_users = self.relationship_service.get_following_user_list(user.id)
        add_filter = {"author__in": following_users}

        following_tasted_records = self.get_feed_queryset(user, add_filter, None)
        unfollowing_tasted_records = self.get_unfollowing_feed(user)

        tasted_records = list(chain(following_tasted_records, unfollowing_tasted_records))

        if request:
            tasted_records = get_not_viewed_contents(request, tasted_records, "tasted_record_viewed")

        return tasted_records

    @transaction.atomic
    def create_record(self, user, validated_data):
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
    def update_record(self, tasted_record: TastedRecord, validated_data):
        """시음기록 업데이트"""

        for attr, value in validated_data.items():
            if attr not in ["bean", "taste_review", "photos"]:
                setattr(tasted_record, attr, value)

        self._set_tasted_record_relations(tasted_record, validated_data)

        tasted_record.save()
        return tasted_record

    @transaction.atomic
    def delete_record(self, tasted_record: TastedRecord):
        """시음기록 삭제"""
        # TODO: bean 데이터 비지니스 로직 추가
        tasted_record.delete()

    def _set_tasted_record_relations(self, tasted_record: TastedRecord, data: dict):
        """시음기록 관계 데이터 설정"""
        if bean_data := data.get("bean"):
            bean = self.bean_service.update(bean_data, tasted_record.author)
            tasted_record.bean = bean

        if taste_review_data := data.get("taste_review"):
            taste_review, _ = BeanTasteReview.objects.update_or_create(
                id=tasted_record.taste_review_id,
                defaults=taste_review_data,
            )
            tasted_record.taste_review = taste_review

        if photos := data.get("photos"):
            tasted_record.photo_set.set(photos)

    # 피드 조회 관련 메서드

    def get_base_record_list_queryset(self, user: Optional[CustomUser] = None) -> QuerySet[TastedRecord]:
        """공통적으로 사용하는 기본 시음기록 리스트 쿼리셋 생성"""
        base_queryset = (
            TastedRecord.objects.select_related("author", "bean", "taste_review")
            .prefetch_related("comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .annotate(
                likes=Count("like_cnt", distinct=True),
                comments=Count("comment", distinct=True),
            )
        )

        if user:
            base_queryset = base_queryset.annotate(
                is_user_liked=Exists(self.like_service.get_like_subquery_for_tasted_record(user)),
                is_user_noted=Exists(self.note_service.get_note_subquery_for_tasted_record(user)),
            )

        return base_queryset

    def get_feed_queryset(
        self, user: CustomUser, add_filter: Optional[Dict] = None, exclude_filter: Optional[Dict] = None, **kwargs
    ) -> QuerySet[TastedRecord]:
        """
        시음기록 피드 쿼리셋 조회

        Args:
            user: 사용자 객체
            add_filter: 추가할 필터 조건 (dict)
            exclude_filter: 제외할 필터 조건 (dict)

        Returns:
            QuerySet: 필터링된 시음기록 쿼리셋
        """
        base_queryset = self.get_base_record_list_queryset(user)

        filters = Q(**add_filter) if add_filter else Q()
        excludes = Q(**exclude_filter) if exclude_filter else Q()

        if user:
            # 차단한 유저 필터링
            filters &= ~Q(author__in=self.relationship_service.get_unique_blocked_user_list(user.id))
        # 비공개 시음기록 필터링
        filters &= Q(is_private=False)

        return base_queryset.filter(filters).exclude(excludes)

    def get_following_feed(self, user: CustomUser) -> QuerySet[TastedRecord]:
        """팔로잉한 사용자의 피드 쿼리셋 조회"""
        following_users = self.relationship_service.get_following_user_list(user.id)

        add_filter = {"author__in": following_users}

        return self.get_feed_queryset(user, add_filter, None)

    # home following feed
    def get_following_feed_and_gte_one_hour(self, user: CustomUser) -> QuerySet[TastedRecord]:
        one_hour_ago = timezone.now() - timedelta(hours=1)
        add_filter = {"created_at__gte": one_hour_ago}

        return self.get_following_feed(user, add_filter, None, None)

    # home common feed
    def get_unfollowing_feed(self, user: CustomUser) -> QuerySet[TastedRecord]:
        """팔로잉하지 않은 사용자의 피드 조회"""
        following_users = self.relationship_service.get_following_user_list(user.id)
        exclude_filter = {"author__in": following_users}

        return self.get_feed_queryset(user, None, exclude_filter)

    # home refresh feed
    def get_refresh_feed(self, user: CustomUser) -> QuerySet[TastedRecord]:
        """새로고침용 피드 조회"""
        return self.get_feed_queryset(user, None, None)

    # 비로그인 사용자 시음기록 피드 조회
    def get_record_list_for_anonymous(self) -> QuerySet[TastedRecord]:
        """비로그인 사용자 시음기록 피드 조회"""
        return (
            TastedRecord.objects.filter(is_private=False)
            .select_related("author", "bean", "taste_review")
            .prefetch_related("comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .annotate(
                likes=Count("like_cnt", distinct=True),
                comments=Count("comment", distinct=True),
                is_user_liked=Value(False, output_field=BooleanField()),  # False 고정
                is_user_noted=Value(False, output_field=BooleanField()),  # False 고정
            )
            .order_by("?")
        )
