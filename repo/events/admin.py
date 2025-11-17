from django.contrib import admin

from repo.events.models import EventCompletion, InternalEvent, PromotionalEvent


@admin.register(PromotionalEvent)
class PromotionalEventAdmin(admin.ModelAdmin):
    """프로모션 이벤트 관리자 페이지"""

    list_display = [
        "event_key",
        "title",
        "status",
        "start_date",
        "end_date",
        "is_commercial",
        "company_name",
        "created_at",
    ]
    list_filter = ["status", "is_commercial", "start_date", "end_date", "created_at"]
    search_fields = ["event_key", "title", "company_name", "purpose"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "event_key",
                    "title",
                    "content",
                    "purpose",
                )
            },
        ),
        (
            "상업 정보",
            {
                "fields": (
                    "is_commercial",
                    "company_name",
                )
            },
        ),
        (
            "기간 설정",
            {
                "fields": (
                    "start_date",
                    "end_date",
                )
            },
        ),
        (
            "미디어 및 링크",
            {
                "fields": (
                    "icon",
                    "external_link",
                )
            },
        ),
        (
            "상태",
            {"fields": ("status",)},
        ),
        (
            "메타 정보",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """event_key 필드에 help_text 추가"""
        form = super().get_form(request, obj, **kwargs)
        if "event_key" in form.base_fields:
            form.base_fields["event_key"].help_text = "Walla projectID를 입력하세요 (예: ge8dEyIwp4z4X2vLESaG)"
        return form


@admin.register(InternalEvent)
class InternalEventAdmin(admin.ModelAdmin):
    """내부 이벤트 관리자 페이지"""

    list_display = ["event_key", "title", "status", "priority", "created_at"]
    list_filter = ["status", "priority", "created_at"]
    search_fields = ["event_key", "title", "content"]
    ordering = ["-priority", "-created_at"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "기본 정보",
            {
                "fields": (
                    "event_key",
                    "title",
                    "content",
                    "priority",
                )
            },
        ),
        (
            "조건 설정",
            {"fields": ("condition",)},
        ),
        (
            "미디어",
            {"fields": ("icon",)},
        ),
        (
            "상태",
            {"fields": ("status",)},
        ),
        (
            "메타 정보",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """event_key 필드에 help_text 추가"""
        form = super().get_form(request, obj, **kwargs)
        if "event_key" in form.base_fields:
            form.base_fields["event_key"].help_text = "내부 이벤트 식별 키를 입력하세요"
        return form


@admin.register(EventCompletion)
class EventCompletionAdmin(admin.ModelAdmin):
    """이벤트 완료 기록 관리자 페이지 (읽기 전용)"""

    list_display = [
        "id",
        "get_user_email",
        "get_event_key",
        "get_event_type",
        "is_agree",
        "completed_at",
    ]
    list_filter = ["is_agree", "completed_at"]
    search_fields = ["user__email", "user__nickname"]
    ordering = ["-completed_at"]
    readonly_fields = [
        "user",
        "internal_event",
        "promotional_event",
        "is_agree",
        "content",
        "completed_at",
    ]

    def has_add_permission(self, request):
        """생성 권한 없음"""
        return False

    def has_change_permission(self, request, obj=None):
        """수정 권한 없음"""
        return False

    def has_delete_permission(self, request, obj=None):
        """삭제 권한 없음 (조회만 가능)"""
        return False

    def get_user_email(self, obj):
        """사용자 이메일 반환"""
        return obj.user.email if obj.user else "-"

    get_user_email.short_description = "사용자 이메일"

    def get_event_key(self, obj):
        """이벤트 키 반환"""
        event = obj.promotional_event or obj.internal_event
        return event.event_key if event else "-"

    get_event_key.short_description = "이벤트 키"

    def get_event_type(self, obj):
        """이벤트 타입 반환"""
        if obj.promotional_event:
            return "프로모션"
        elif obj.internal_event:
            return "내부"
        return "-"

    get_event_type.short_description = "이벤트 타입"

    fieldsets = (
        (
            "사용자 정보",
            {"fields": ("user",)},
        ),
        (
            "이벤트 정보",
            {
                "fields": (
                    "promotional_event",
                    "internal_event",
                )
            },
        ),
        (
            "완료 정보",
            {
                "fields": (
                    "is_agree",
                    "completed_at",
                    "content",
                )
            },
        ),
    )
