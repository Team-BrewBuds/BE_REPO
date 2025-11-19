from rest_framework import serializers

from repo.events.enums import EventType
from repo.events.models import EventCompletion, InternalEvent, PromotionalEvent


class PromotionalEventDataSerializer(serializers.ModelSerializer):
    """프로모션 이벤트 data 필드용 serializer"""

    class Meta:
        model = PromotionalEvent
        fields = [
            "title",
            "content",
            "icon",
            "external_link",
            "start_date",
            "end_date",
            "is_commercial",
            "company_name",
            "purpose",
        ]


class InternalEventDataSerializer(serializers.ModelSerializer):
    """내부 이벤트 data 필드용 serializer"""

    class Meta:
        model = InternalEvent
        fields = [
            "title",
            "content",
            "icon",
            "priority",
            "condition",
        ]


class UnifiedEventSerializer(serializers.Serializer):
    """통합 이벤트 응답용 serializer (타입별 중첩 구조)"""

    id = serializers.CharField(source="event_key", read_only=True)
    event_type = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True, default=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    data = serializers.SerializerMethodField()

    def get_event_type(self, obj):
        """이벤트 타입 반환"""
        if isinstance(obj, PromotionalEvent):
            return EventType.PROMOTIONAL.value
        elif isinstance(obj, InternalEvent):
            return EventType.INTERNAL.value
        return None

    def get_data(self, obj):
        """이벤트 타입에 따라 적절한 serializer로 data 반환"""
        if isinstance(obj, PromotionalEvent):
            return PromotionalEventDataSerializer(obj).data
        elif isinstance(obj, InternalEvent):
            return InternalEventDataSerializer(obj).data
        return None


class EventCompletionSerializer(serializers.ModelSerializer):
    """완료 기록 조회용 serializer"""

    event_type = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()

    class Meta:
        model = EventCompletion
        fields = ["id", "event_type", "completed_at", "event"]

    def get_event_type(self, obj):
        """이벤트 타입 반환"""
        if obj.promotional_event:
            return EventType.PROMOTIONAL.value
        elif obj.internal_event:
            return EventType.INTERNAL.value
        return None

    def get_event(self, obj):
        """완료된 이벤트 정보 반환"""
        event = obj.promotional_event or obj.internal_event
        if event:
            return UnifiedEventSerializer(event).data
        return None


class EventCompletionResponseSerializer(serializers.Serializer):
    """완료 API 응답용 serializer"""

    message = serializers.CharField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)


class EventCompleteRequestSerializer(serializers.Serializer):
    """Webhook 이벤트 완료 요청용 serializer"""

    projectKey = serializers.CharField(required=True, help_text="projectID")  # noqa: N815
    nickname = serializers.CharField(required=True, help_text="사용자 닉네임")
    email = serializers.EmailField(required=True, help_text="사용자 이메일")
    phone = serializers.CharField(required=True, help_text="사용자 전화번호")
    timestamp = serializers.DateTimeField(required=True, help_text="완료 시간")
    is_agree = serializers.BooleanField(required=True, help_text="사용자 동의 여부")

    def validate(self, attrs):
        """나머지 필드는 content로 저장"""
        # 기본 필드 외의 모든 필드를 content로 저장
        content = {}
        for key, value in self.initial_data.items():
            if key not in ["projectKey", "timestamp", "is_agree"]:
                content[key] = value
        attrs["content"] = content
        return attrs
