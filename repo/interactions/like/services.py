from django.db.models import OuterRef

from repo.common.exception.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from repo.records.models import Comment, Post, TastedRecord


class LikeService:
    """
    좋아요 관련 비즈니스 로직을 처리하는 서비스 클래스

    Attributes:
        like_repo: 좋아요 대상 객체 (Post, TastedRecord, Comment)
    """

    model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}

    def __init__(self, object_type: str, object_id: int = None):
        self.like_repo = self._set_like_object(object_type, object_id)
        self.target_model = self.model_map[object_type]
        self.object_type = object_type
        self.object_id = object_id

    def _set_like_object(self, object_type: str, object_id: int):
        if object_type not in self.model_map:
            raise ValidationException(detail="Invalid object type", code="validation_error")

        if object_id is None:  # 좋아요 대상 객체가 없는 경우
            return None

        try:
            return self.target_model.objects.get(id=object_id)
        except self.target_model.DoesNotExist as e:
            raise NotFoundException(detail="object not found", code="not_found") from e

    def increase_like(self, user_id: int) -> None:
        """좋아요 증가"""

        if self.like_repo.like_cnt.filter(id=user_id).exists():
            raise ConflictException(detail="like already exists", code="conflict")

        self.like_repo.like_cnt.add(user_id)

    def decrease_like(self, user_id: int) -> None:
        """좋아요 감소"""
        if not self.like_repo.like_cnt.filter(id=user_id).exists():
            raise NotFoundException(detail="like not found", code="not_found")

        self.like_repo.like_cnt.remove(user_id)

    def get_like_count(self) -> int:
        """좋아요 개수 반환"""
        # TODO: 캐시 적용 필요
        return self.like_repo.like_cnt.count()

    def is_user_liked(self, user_id: int) -> bool:
        """사용자가 좋아요를 눌렀는지 여부 반환"""
        return self.like_repo.like_cnt.filter(id=user_id).exists()

    def get_like_subquery_for_post(self, user):
        return self.target_model.like_cnt.through.objects.filter(post_id=OuterRef("pk"), customuser_id=user.id)

    def get_like_subquery_for_tasted_record(self, user):
        return self.target_model.like_cnt.through.objects.filter(tastedrecord_id=OuterRef("pk"), customuser_id=user.id)
