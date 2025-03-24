from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationSetting, PushNotification, UserDevice
from .schemas import NotificationSchema
from .serializers import (
    NotificationSettingsSerializer,
    PushNotificationSerializer,
    UserDeviceSerializer,
)
from .services import FCMService


@NotificationSchema.notification_test_schema_view
class NotificationTestAPIView(APIView):
    """
    푸시 알림 테스트용 API
    """

    def post(self, request, token):
        fcm_service = FCMService()
        fcm_service.send_push_notification_to_single_device(
            device_token=token, title="브루버즈", body="테스트 알림입니다.", data={"test": "true"}
        )
        return Response({"message": "테스트 알림이 전송되었습니다."}, status=status.HTTP_200_OK)


@NotificationSchema.user_notification_schema_view
class UserNotificationAPIView(APIView):
    """
    사용자별 푸시 알림 관리 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """사용자의 알림 목록 조회"""
        device = UserDevice.objects.get(user=request.user)
        notifications = PushNotification.objects.filter(device=device).order_by("-id")

        serializer = PushNotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """사용자의 알림 전체 읽음 처리"""
        device = UserDevice.objects.get(user=request.user)
        PushNotification.objects.filter(device=device).update(is_read=True)
        return Response({"message": "사용자의 알림이 모두 읽음 처리되었습니다."}, status=status.HTTP_200_OK)

    def delete(self, request):
        """사용자의 알림 전체 삭제"""
        device = UserDevice.objects.get(user=request.user)
        PushNotification.objects.filter(device=device).delete()
        return Response({"message": "사용자의 알림이 모두 삭제되었습니다."}, status=status.HTTP_200_OK)


@NotificationSchema.notification_setting_schema_view
class NotificationSettingAPIView(APIView):
    """
    알림 설정 관리 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """알림 설정 조회"""
        settings = NotificationSetting.objects.get(user=request.user)
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        알림 설정 생성 (회원가입 시 설정)
        """
        settings = NotificationSetting.objects.create(user=request.user)
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        """알림 설정 수정"""
        settings = NotificationSetting.objects.get(user=request.user)
        serializer = NotificationSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@NotificationSchema.user_device_token_schema_view
class NotificationTokenAPIView(APIView):
    """
    사용자 디바이스 토큰 관리 API
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """사용자의 디바이스 토큰 저장 횩은 갱신"""
        serializer = UserDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token, created = UserDevice.objects.update_or_create(
            user=request.user,
            defaults=serializer.validated_data,
        )

        message = "user device token" + "created" if created else "updated"
        return Response({"message": message}, status=status.HTTP_200_OK)

    def delete(self, request):
        """사용자의 디바이스 토큰 삭제"""
        UserDevice.objects.filter(user=request.user, is_active=True).delete()
        return Response({"message": "user device token deleted"}, status=status.HTTP_204_NO_CONTENT)
