from django.db import models

from repo.profiles.models import CustomUser


class Report(models.Model):
    class ReportStatus(models.TextChoices):
        PENDING = "pending", "대기 중"
        PROCESSING = "processing", "처리 중"
        COMPLETED = "completed", "완료됨"

    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="신고자")
    reason = models.TextField(verbose_name="신고 사유")
    status = models.CharField(max_length=50, choices=ReportStatus.choices, default=ReportStatus.PENDING, verbose_name="신고 처리 상태")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="신고 일자")

    def __str__(self):
        return f"Report: {self.id} - {self.get_status_display()}"

    class Meta:
        abstract = True


class ContentReport(Report):
    class ReportObjectType(models.TextChoices):
        POST = "post", "게시글"
        COMMENT = "comment", "댓글"
        TASTED_RECORD = "tasted_record", "시음 기록"

    object_type = models.CharField(max_length=50, choices=ReportObjectType.choices, verbose_name="신고 대상 종류")
    object_id = models.PositiveIntegerField(verbose_name="신고 대상 ID")

    def __str__(self):
        return f"ContentReport: {self.id} - {self.get_object_type_display()}"

    class Meta:
        db_table = "content_report"
        verbose_name = "콘텐츠 신고"
        verbose_name_plural = "콘텐츠 신고"


class UserReport(Report):
    target_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reported_users", verbose_name="신고 대상 유저")

    def __str__(self):
        return f"UserReport: {self.id} - {self.target_user.nickname}"

    class Meta:
        db_table = "user_report"
        verbose_name = "유저 신고"
        verbose_name_plural = "유저 신고"
