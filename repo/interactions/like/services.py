import logging

from django.db import transaction
from django.db.models import F, OuterRef

from repo.common.exception.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from repo.common.utils import get_object_by_type
from repo.notifications.services import NotificationService
from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord

logger = logging.getLogger("django.server")


class LikeService:
    """
    좋아요 관련 비즈니스 로직을 처리하는 서비스 클래스

    Attributes:
        like_repo: 좋아요 대상 객체 (Post, TastedRecord, Comment)
        target_model: 좋아요 대상 모델 클래스
        object_type: 좋아요 대상 객체 타입
        object_id: 좋아요 대상 객체 ID
    """

    model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}

    def __init__(self, object_type: str, object_id: int = None):
        if object_type not in self.model_map:
            raise ValidationException(detail="Invalid object type", code="validation_error")

        self.target_model: Post | TastedRecord | Comment = self.model_map[object_type]
        self.object_type = object_type
        self.object_id = object_id
        self.like_repo = self._set_like_object()
        self.notification_service = NotificationService()

    def _set_like_object(self) -> Post | TastedRecord | Comment | None:
        """좋아요 대상 객체 설정"""
        if self.object_id is None:  # 좋아요 대상 객체가 없는 경우
            return None

        try:
            return self.target_model.objects.get(id=self.object_id)
        except self.target_model.DoesNotExist as e:
            raise NotFoundException(detail="object not found", code="not_found") from e

    @transaction.atomic
    def increase_like(self, user_id: int) -> None:
        """좋아요 증가"""

        if self.like_repo.like_cnt.filter(id=user_id).exists():
            raise ConflictException(detail="like already exists", code="conflict")

        self.like_repo.like_cnt.add(user_id)

        self.target_model.objects.filter(id=self.like_repo.id).select_for_update(of=["self"]).values("likes").update(likes=F("likes") + 1)

        # 알림 전송
        try:
            liked_user = CustomUser.objects.get(id=user_id)
            liked_obj = get_object_by_type(self.object_type, self.object_id)

            notification_service = NotificationService()
            is_sent = notification_service.send_notification_like(liked_obj, liked_user)

            if not is_sent:
                return

            logger.info(f"좋아요({self.like_repo.id}) 알림 전송 완료")
            return {
                "status": "success",
                "liked_obj_type": self.object_type,
                "liked_obj_id": self.object_id,
                "liked_user_id": user_id,
            }

        except CustomUser.DoesNotExist:
            logger.error(f"좋아요({self.like_repo.id}) 알림 전송 실패: 사용자를 찾을 수 없습니다")
            return {"status": "error", "message": "사용자를 찾을 수 없습니다"}

        except Exception as e:
            logger.error(f"좋아요({self.like_repo.id}) 알림 전송 실패: {str(e)}")
            return {"status": "retrying", "message": str(e)}

    @transaction.atomic
    def decrease_like(self, user_id: int) -> None:
        """좋아요 감소"""
        if not self.like_repo.like_cnt.filter(id=user_id).exists():
            raise NotFoundException(detail="like not found", code="not_found")

        if self.like_repo.likes == 0:
            raise ValidationException(detail="like count is 0", code="invalid_like_count")

        self.like_repo.like_cnt.remove(user_id)

        self.target_model.objects.filter(id=self.like_repo.id).select_for_update(of=["self"]).values("likes").update(likes=F("likes") - 1)

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
