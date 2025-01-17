from abc import ABC, abstractmethod

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model

from repo.common.exception.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord

from .models import ContentReport, Report, UserReport


class AbstractReportService(ABC):
    """신고 관련 서비스의 추상 기본 클래스"""

    def __init__(self):
        self.model: type[Report] = None

    def create(self, user: CustomUser, reason: str, **kwargs) -> Report:
        """신고 생성"""
        if self._is_existing_report(user, **kwargs):
            raise ConflictException(detail="report already exists", code="report_exists")

        if self._is_self_report(user, **kwargs):
            raise ConflictException(detail="self report is not allowed", code="self_report_not_allowed")

        return self._create_report(user, reason, **kwargs)

    def set_processing_status(self, report: Report) -> Report:
        """신고 처리 상태를 처리 중으로 변경"""
        report.status = Report.ReportStatus.PROCESSING
        report.save()
        return report

    def set_completed_status(self, report: Report) -> Report:
        """신고 처리 상태를 완료됨으로 변경"""
        report.status = Report.ReportStatus.COMPLETED
        report.save()
        return report

    @abstractmethod
    def _is_existing_report(self, user: CustomUser, **kwargs) -> bool:
        """이미 신고한 내역이 있는지 확인"""
        pass

    @abstractmethod
    def _is_self_report(self, user: CustomUser, **kwargs) -> bool:
        """자기 자신을 신고하는지 확인"""
        pass

    @abstractmethod
    def _create_report(self, user: CustomUser, reason: str, **kwargs) -> Report:
        """신고 생성 구현"""
        pass

    @abstractmethod
    def get_target_author(self, **kwargs) -> str:
        """신고 대상자의 닉네임 조회"""
        pass


class ContentReportService(AbstractReportService):
    """콘텐츠 신고 관련 서비스"""

    def __init__(self):
        super().__init__()
        self.model = ContentReport
        self.model_map: dict[str, type[Model]] = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}

    def _get_instance(self, object_type: str, object_id: int) -> Model:
        """신고 대상 객체 조회"""
        if object_type not in self.model_map:
            raise ValidationException(detail=f"Invalid object type: {object_type}", code="invalid_object_type")

        try:
            return self.model_map[object_type].objects.select_related("author").get(id=object_id)
        except ObjectDoesNotExist as e:
            raise NotFoundException(detail=f"{object_type} with id {object_id} not found", code="object_not_found") from e

    def _is_existing_report(self, user: CustomUser, object_type: str, object_id: int) -> bool:
        return self.model.objects.filter(author=user, object_type=object_type, object_id=object_id).exists()

    def _is_self_report(self, user: CustomUser, object_type: str, object_id: int) -> bool:
        target_object = self._get_instance(object_type, object_id)
        return target_object.author == user

    def _create_report(self, user: CustomUser, reason: str, object_type: str, object_id: int) -> ContentReport:
        return self.model.objects.create(
            author=user, object_type=object_type, object_id=object_id, reason=reason, status=Report.ReportStatus.PENDING
        )

    def get_target_author(self, object_type: str, object_id: int) -> str:
        target_object = self._get_instance(object_type, object_id)
        return target_object.author.nickname


class UserReportService(AbstractReportService):
    """유저 신고 관련 서비스"""

    def __init__(self):
        super().__init__()
        self.model = UserReport

    def _is_existing_report(self, user: CustomUser, target_user_id: int) -> bool:
        return self.model.objects.filter(author=user, target_user_id=target_user_id).exists()

    def _is_self_report(self, user: CustomUser, target_user_id: int) -> bool:
        return user.id == target_user_id

    def _create_report(self, user: CustomUser, reason: str, target_user_id: int) -> UserReport:
        try:
            target_user = CustomUser.objects.get(id=target_user_id)
        except ObjectDoesNotExist as e:
            raise NotFoundException(detail=f"User with id {target_user_id} not found", code="user_not_found") from e

        return self.model.objects.create(author=user, target_user=target_user, reason=reason, status=Report.ReportStatus.PENDING)

    def get_target_author(self, target_user_id: int) -> str:
        try:
            target_user = CustomUser.objects.get(id=target_user_id)
            return target_user.nickname
        except ObjectDoesNotExist as e:
            raise NotFoundException(detail=f"User with id {target_user_id} not found", code="user_not_found") from e
