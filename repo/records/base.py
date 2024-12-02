from abc import ABC, abstractmethod
from typing import Dict, Optional

from django.db.models import QuerySet

from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


class BaseRecordService(ABC):
    """레코드(Post/TastedRecord) 서비스의 추상 기본 클래스"""

    def __init__(self, relationship_service, like_service, note_service):
        self.relationship_service = relationship_service
        self.like_service = like_service
        self.note_service = note_service

    @abstractmethod
    def get_record_detail(self, pk: int) -> Post | TastedRecord:
        """게시물 상세 조회"""
        pass

    @abstractmethod
    def get_user_records(self, user_id: int, **kwargs) -> QuerySet[Post | TastedRecord]:
        """유저가 작성한 게시물 조회"""
        pass

    @abstractmethod
    def get_record_list(self, user: CustomUser, **kwargs) -> QuerySet[Post | TastedRecord]:
        """게시물 리스트 조회"""
        pass

    @abstractmethod
    def create_record(self, user: CustomUser, validated_data: dict) -> Post | TastedRecord:
        """게시물 생성"""
        pass

    @abstractmethod
    def update_record(self, record: Post | TastedRecord, validated_data: dict) -> Post | TastedRecord:
        """게시물 수정"""
        pass

    @abstractmethod
    def delete_record(self, record: Post | TastedRecord):
        """게시물 삭제"""
        pass

    @abstractmethod
    def get_base_record_list_queryset(self, user: Optional[CustomUser] = None) -> QuerySet[Post | TastedRecord]:
        """공통적으로 사용하는 기본 게시물 리스트 쿼리셋 생성"""
        pass

    @abstractmethod
    def get_feed_queryset(
        self, user: CustomUser, add_filter: Optional[Dict] = None, exclude_filter: Optional[Dict] = None, **kwargs
    ) -> QuerySet[Post | TastedRecord]:
        """피드 쿼리셋 조회"""
        pass

    @abstractmethod
    def get_following_feed(self, user: CustomUser, following_users: QuerySet[CustomUser]) -> QuerySet[Post | TastedRecord]:
        """팔로잉 피드 조회"""
        pass

    @abstractmethod
    def get_record_list_for_anonymous(self) -> QuerySet[Post | TastedRecord]:
        """비로그인 사용자 피드 조회"""
        pass