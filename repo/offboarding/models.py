import datetime

from django.db import models

from repo.profiles.models import CustomUser

# TODO: 마감일 확정 후 수정 필요
EXPORT_REQUEST_DEADLINE = datetime.date(2099, 12, 31)


class ExportRequest(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="export_request",
        verbose_name="사용자",
    )
    export_email = models.EmailField(verbose_name="데이터 전송 이메일")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="신청일")

    class Meta:
        db_table = "export_request"
        verbose_name = "데이터 전송 신청"
        verbose_name_plural = "데이터 전송 신청 목록"
