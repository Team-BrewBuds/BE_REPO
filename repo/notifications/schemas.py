from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from .serializers import NotificationSettingsSerializer, PushNotificationSerializer

NOTIFICATION_TAG = "notifications"


class NotificationSchema:
    """
    알림 관련 API 스키마
    """

    test_notification_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="FCM 디바이스 토큰",
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="알림 전송 성공",
                response={"type": "object", "properties": {"message": {"type": "string"}}},
            ),
        },
        summary="푸시 알림 테스트",
        description="""
            FCM 토큰을 사용하여 테스트 알림을 전송합니다.

            담당자: hwstar1204
        """,
        tags=[NOTIFICATION_TAG],
    )

    user_notification_get_schema = extend_schema(
        summary="사용자 알림 목록 조회",
        description="""
            현재 로그인한 사용자의 알림 목록을 조회합니다.

            담당자: hwstar1204
        """,
        responses={
            200: PushNotificationSerializer(many=True),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    user_notification_post_schema = extend_schema(
        summary="알림 전체 읽음 처리",
        description="""
            사용자의 모든 알림을 읽음 처리합니다.

            담당자: hwstar1204
        """,
        responses={
            200: OpenApiResponse(
                description="읽음 처리 성공",
                response={"type": "object", "properties": {"message": {"type": "string"}}},
            ),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    user_notification_delete_schema = extend_schema(
        summary="알림 전체 삭제",
        description="""
            사용자의 모든 알림을 삭제합니다.

            담당자: hwstar1204
        """,
        responses={
            200: OpenApiResponse(
                description="삭제 성공",
                response={"type": "object", "properties": {"message": {"type": "string"}}},
            ),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    settings_get_schema = extend_schema(
        summary="알림 설정 조회",
        description="""
            사용자의 알림 설정을 조회합니다.

            담당자: hwstar1204
        """,
        responses={
            200: NotificationSettingsSerializer,
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    settings_post_schema = extend_schema(
        summary="알림 설정 생성",
        description="""
            사용자의 알림 설정을 생성합니다.

            담당자: hwstar1204
        """,
        request=NotificationSettingsSerializer,
        responses={
            201: NotificationSettingsSerializer,
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    settings_patch_schema = extend_schema(
        summary="알림 설정 수정",
        description="""
            사용자의 알림 설정을 수정합니다.

            담당자: hwstar1204
        """,
        request=NotificationSettingsSerializer,
        responses={
            200: NotificationSettingsSerializer,
            400: OpenApiResponse(
                description="유효하지 않은 요청",
                response={"type": "object", "properties": {"error": {"type": "string"}}},
            ),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    notification_test_schema_view = extend_schema_view(post=test_notification_schema)

    user_notification_schema_view = extend_schema_view(
        get=user_notification_get_schema,
        post=user_notification_post_schema,
        delete=user_notification_delete_schema,
    )

    notification_settings_schema_view = extend_schema_view(
        get=settings_get_schema,
        post=settings_post_schema,
        patch=settings_patch_schema,
    )
