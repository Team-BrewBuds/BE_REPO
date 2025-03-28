from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer

from .serializers import (
    NotificationSettingsSerializer,
    NotificationTestSerializer,
    PushNotificationSerializer,
    UserDeviceSerializer,
)

NOTIFICATION_TAG = "notifications"


class NotificationSchema:
    """
    알림 관련 API 스키마
    """

    user_notification_get_schema = extend_schema(
        parameters=[PageNumberSerializer],
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

    user_notification_patch_schema = extend_schema(
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

    user_notification_detail_patch_schema = extend_schema(
        summary="개별 알림 읽음 처리",
        description="""
            개별 알림을 읽음 처리합니다.
        """,
        tags=[NOTIFICATION_TAG],
    )

    user_notification_detail_delete_schema = extend_schema(
        summary="개별 알림 삭제",
        description="""
            개별 알림을 삭제합니다.
        """,
        tags=[NOTIFICATION_TAG],
    )

    notification_setting_get_schema = extend_schema(
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

    notification_setting_post_schema = extend_schema(
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

    notification_setting_patch_schema = extend_schema(
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

    user_device_token_post_schema = extend_schema(
        summary="사용자의 디바이스 토큰 저장 혹은 갱신",
        description="""
            사용자의 디바이스 토큰을 생성 합니다. (로그인 시 호출)
            이미 존재하는 디바이스 토큰인 경우 갱신됩니다.

            담당자: hwstar1204
        """,
        request=UserDeviceSerializer,
        responses={
            200: OpenApiResponse(description="디바이스 토큰 생성 혹은 갱신 성공"),
            400: OpenApiResponse(description="유효하지 않은 요청"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    user_device_token_delete_schema = extend_schema(
        summary="사용자의 디바이스 토큰 비활성화",
        description="""
            사용자의 디바이스 토큰을 비활성화 합니다. (로그아웃 시 호출)

            body = {
                "device_token": "디바이스 토큰",
                "device_type": "디바이스 타입"  # "ios" 또는 "android"
            }

            담당자: hwstar1204
        """,
        request=UserDeviceSerializer,
        responses={
            204: OpenApiResponse(description="디바이스 토큰 비활성화 성공"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=[NOTIFICATION_TAG],
    )

    test_notification_schema = extend_schema(
        request=NotificationTestSerializer,
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

    notification_test_schema_view = extend_schema_view(post=test_notification_schema)

    user_notification_schema_view = extend_schema_view(
        get=user_notification_get_schema,
        patch=user_notification_patch_schema,
        delete=user_notification_delete_schema,
    )

    user_notification_detail_schema_view = extend_schema_view(
        patch=user_notification_detail_patch_schema,
        delete=user_notification_detail_delete_schema,
    )

    notification_setting_schema_view = extend_schema_view(
        get=notification_setting_get_schema,
        post=notification_setting_post_schema,
        patch=notification_setting_patch_schema,
    )

    user_device_token_schema_view = extend_schema_view(
        post=user_device_token_post_schema,
        delete=user_device_token_delete_schema,
    )
