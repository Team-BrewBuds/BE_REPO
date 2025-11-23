from django.db import models

from repo.events.enums import EventStatus
from repo.profiles.models import CustomUser


class BaseEvent(models.Model):
    """이벤트 기본 모델"""

    event_key = models.CharField(max_length=100, primary_key=True, verbose_name="이벤트 키", help_text="projectID를 입력하세요")
    status = models.CharField(max_length=10, choices=EventStatus.values(), default=EventStatus.READY, verbose_name="상태")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["event_key"]),
        ]


class InternalEvent(BaseEvent):
    """내부조건형 이벤트"""

    title = models.CharField(max_length=100, verbose_name="제목")
    content = models.CharField(max_length=255, verbose_name="내용")
    icon = models.ImageField(upload_to="event_icons/", null=True, blank=True, verbose_name="아이콘")
    priority = models.IntegerField(default=0, verbose_name="우선순위", help_text="우선순위 (높을수록 우선)")
    condition = models.JSONField(verbose_name="달성 조건")

    class Meta:
        db_table = "internal_events"
        ordering = ["-priority", "event_key"]
        verbose_name = "내부조건형 이벤트"
        verbose_name_plural = "내부조건형 이벤트"

    def __str__(self):
        return f"[내부] {self.event_key}"


class PromotionalEvent(BaseEvent):
    """프로모션형 이벤트"""

    is_commercial = models.BooleanField(default=False, verbose_name="상업 여부")
    company_name = models.CharField(max_length=20, blank=True, null=True, verbose_name="업체명")
    purpose = models.CharField(max_length=20, verbose_name="목적")
    title = models.CharField(max_length=100, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    start_date = models.DateTimeField(verbose_name="시작일")
    end_date = models.DateTimeField(verbose_name="종료일")
    icon = models.ImageField(upload_to="event_icons/", null=True, blank=True, verbose_name="아이콘")
    external_link = models.URLField(verbose_name="외부링크 (캠페인 URL)")

    class Meta:
        db_table = "promotional_events"
        ordering = ["event_key"]  # 최신순
        verbose_name = "프로모션형 이벤트"
        verbose_name_plural = "프로모션형 이벤트"
        indexes = [
            models.Index(fields=["status", "start_date", "end_date"]),
        ]

    def __str__(self):
        return f"[프로모션] {self.title}"

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("종료일은 시작일보다 커야 합니다.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EventCompletion(models.Model):
    """이벤트 완료 기록 (이벤트 타입별로 분리)"""

    internal_event = models.ForeignKey(InternalEvent, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="completions")
    promotional_event = models.ForeignKey(PromotionalEvent, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="completions")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="completed_events")
    phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="사용자 전화번호")
    is_agree = models.BooleanField(default=True, verbose_name="사용자 동의 여부")
    content = models.JSONField(default=dict, blank=True, verbose_name="폼 제출 내용")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="완료 시간")

    class Meta:
        db_table = "event_completions"
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(internal_event__isnull=False, promotional_event__isnull=True)
                    | models.Q(internal_event__isnull=True, promotional_event__isnull=False)
                ),
                name="only_one_event_type",
            ),
            # 사용자당 프로모션 이벤트 중복 참여 방지
            models.UniqueConstraint(
                fields=["user", "promotional_event"],
                condition=models.Q(promotional_event__isnull=False),
                name="unique_user_promotional_event",
            ),
            # 사용자당 내부 이벤트 중복 참여 방지
            models.UniqueConstraint(
                fields=["user", "internal_event"], condition=models.Q(internal_event__isnull=False), name="unique_user_internal_event"
            ),
        ]
        indexes = [
            models.Index(fields=["user", "internal_event"]),
            models.Index(fields=["user", "promotional_event"]),
        ]
        verbose_name = "이벤트 완료 기록"
        verbose_name_plural = "이벤트 완료 기록"

    def __str__(self):
        event = self.internal_event or self.promotional_event
        return f"{self.user.nickname} - {event}"
