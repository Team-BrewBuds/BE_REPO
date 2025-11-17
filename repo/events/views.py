from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import APIKeyPermission
from repo.events.schemas import (
    EventCompleteSchema,
    EventDetailSchema,
    EventListSchema,
    MyCompletionListSchema,
)
from repo.events.serializers import (
    EventCompleteRequestSerializer,
    EventCompletionResponseSerializer,
    EventCompletionSerializer,
    UnifiedEventSerializer,
)
from repo.events.services import EventService


@EventListSchema.event_list_schema_view
class EventListAPIView(APIView):
    """
    통합 이벤트 목록 조회 API
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_service = EventService()

    def get(self, request):
        """이벤트 목록 조회"""
        event_type = request.query_params.get("event_type", None)
        events = self.event_service.get_active_events(request.user, event_type)
        serializer = UnifiedEventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@EventDetailSchema.event_detail_schema_view
class EventDetailAPIView(APIView):
    """
    통합 이벤트 상세 조회 API
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_service = EventService()

    def get(self, request, event_key):
        """이벤트 상세 조회 (타입 자동 판별)"""
        user = request.user if request.user.is_authenticated else None
        event = self.event_service.get_event_by_key(event_key, user)
        serializer = UnifiedEventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


@EventCompleteSchema.event_complete_schema_view
class EventCompleteAPIView(APIView):
    """
    Webhook 이벤트 참여 완료 기록 API (프로모션만 허용)
    """

    permission_classes = [APIKeyPermission]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_service = EventService()

    def post(self, request):
        """Webhook을 통한 이벤트 완료 처리"""
        serializer = EventCompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data

        completion = self.event_service.complete_event_webhook(
            project_key=validated_data["projectKey"],
            email=validated_data["email"],
            timestamp=validated_data["timestamp"],
            is_agree=validated_data["is_agree"],
            content=validated_data["content"],
        )

        response_data = {
            "message": "이벤트 참여가 완료되었습니다",
            "completed_at": completion.completed_at,
        }
        response_serializer = EventCompletionResponseSerializer(response_data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@MyCompletionListSchema.my_completion_list_schema_view
class MyEventCompletionListAPIView(APIView):
    """
    내 참여 이력 조회 API
    """

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_service = EventService()

    def get(self, request):
        """내 완료 이력 조회"""
        event_type = request.query_params.get("event_type", None)
        completions = self.event_service.get_user_completions(request.user, event_type)
        serializer = EventCompletionSerializer(completions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
