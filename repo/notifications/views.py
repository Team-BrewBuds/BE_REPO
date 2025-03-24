from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.utils import get_paginated_response_with_class

from .models import NotificationSetting, PushNotification, UserDevice
from .schemas import NotificationSchema
from .serializers import (
    NotificationSettingsSerializer,
    PushNotificationSerializer,
    UserDeviceSerializer,
)
from .services import FCMService


@NotificationSchema.user_notification_schema_view
class UserNotificationAPIView(APIView):
    """
    특정 기기의 알림 목록 관리 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """알림 목록 조회"""
        devices = UserDevice.objects.filter(user=request.user, is_active=True)
        notifications = PushNotification.objects.filter(device__in=devices).order_by("-id")
        return get_paginated_response_with_class(request, notifications, PushNotificationSerializer)

    def patch(self, request):
        """알림 전체 읽음 처리"""
        devices = UserDevice.objects.filter(user=request.user, is_active=True)
        PushNotification.objects.filter(device__in=devices, is_read=False).update(is_read=True)
        return Response({"message": "모든 알림이 읽음 처리되었습니다."}, status=status.HTTP_200_OK)

    def delete(self, request):
        """알림 전체 삭제"""
        devices = UserDevice.objects.filter(user=request.user, is_active=True)
        PushNotification.objects.filter(device__in=devices).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@NotificationSchema.user_notification_detail_schema_view
class UserNotificationDetailAPIView(APIView):
    """
    개별 알림 관리 API
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id: int):
        """개별 알림 읽음 처리"""
        notification = get_object_or_404(PushNotification, id=notification_id, device__user=request.user, device__is_active=True)
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, notification_id: int):
        """개별 알림 삭제"""
        notification = get_object_or_404(PushNotification, id=notification_id, device__user=request.user, device__is_active=True)
        notification.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@NotificationSchema.notification_setting_schema_view
class NotificationSettingAPIView(APIView):
    """
    알림 설정 관리 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """알림 설정 조회"""
        settings = get_object_or_404(NotificationSetting, user=request.user)
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """알림 설정 생성

        TODO 회원가입 로직에서 호출되는 것으로 이동 필요
        """
        serializer = NotificationSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        settings, created = NotificationSetting.objects.get_or_create(user=request.user, defaults=serializer.validated_data)

        if not created:
            for key, value in serializer.validated_data.items():
                setattr(settings, key, value)
            settings.save()

        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request):
        """알림 설정 수정"""
        settings = get_object_or_404(NotificationSetting, user=request.user)
        serializer = NotificationSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@NotificationSchema.user_device_token_schema_view
class NotificationTokenAPIView(APIView):
    """
    디바이스 토큰 관리 API
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """디바이스 토큰 등록/갱신"""
        serializer = UserDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_token = serializer.validated_data["device_token"]
        device_type = serializer.validated_data["device_type"]

        device, created = UserDevice.objects.update_or_create(
            user=request.user,
            device_token=device_token,
            defaults={"device_type": device_type, "is_active": True},
        )

        serializer = UserDeviceSerializer(device)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request):
        """디바이스 토큰 비활성화"""
        serializer = UserDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_token = serializer.validated_data["device_token"]
        device_type = serializer.validated_data["device_type"]

        device = get_object_or_404(UserDevice, user=request.user, device_token=device_token, device_type=device_type)
        device.is_active = False
        device.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@NotificationSchema.notification_test_schema_view
class NotificationTestAPIView(APIView):
    """
    푸시 알림 테스트용 API
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """테스트 알림 전송"""
        serializer = UserDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device, created = UserDevice.objects.get_or_create(user=request.user, is_active=True, defaults=serializer.validated_data)

        fcm_service = FCMService()
        fcm_service.send_push_notification_to_single_device(
            device_token=device.device_token, title="브루버즈", body="테스트 알림입니다.", data={"test": "true"}
        )
        return Response({"message": "테스트 알림이 전송되었습니다."}, status=status.HTTP_200_OK)
