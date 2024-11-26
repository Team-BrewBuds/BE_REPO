from django.core.exceptions import ObjectDoesNotExist

from repo.common.exception.exceptions import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from repo.records.models import Comment, Post, TastedRecord

from .models import Report


class ReportService:
    def __init__(self, report_repo=Report.objects):
        self.report_repo = report_repo

    def is_existing_report(self, user, object_type, object_id):
        """이미 신고한 컨텐츠인지 확인"""
        return self.report_repo.filter(author=user, object_type=object_type, object_id=object_id).exists()

    def _get_instance(self, object_type, object_id):
        """신고 대상 객체 조회"""
        model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}

        if object_type not in model_map:
            raise ValidationException(detail=f"Invalid object type: {object_type}", code="invalid_object_type")

        try:
            return model_map[object_type].objects.select_related("author").get(id=object_id)
        except ObjectDoesNotExist as e:
            raise NotFoundException(detail=f"{object_type} with id {object_id} not found", code="object_not_found") from e

    def create(self, user, object_type, object_id, reason):
        """신고 생성"""
        if self.is_existing_report(user, object_type, object_id):
            raise ConflictException(detail="report already exists", code="report_exists")

        target_object = self._get_instance(object_type, object_id)
        if target_object.author == user:
            raise ConflictException(detail="self report is not allowed", code="self_report_not_allowed")

        report = self.report_repo.create(
            author=user, object_type=object_type, object_id=object_id, reason=reason, status=Report.ReportStatus.PENDING
        )

        return report

    def get_target_author(self, object_type, object_id):
        """신고 대상자 조회"""
        target_object = self._get_instance(object_type, object_id)
        return target_object.author.nickname
