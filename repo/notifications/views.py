from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NotificationSettings, PushNotification
from .schemas import NotificationSchema
from .serializers import NotificationSettingsSerializer, PushNotificationSerializer
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
        notifications = PushNotification.objects.filter(user=request.user).order_by("-created_at")

        serializer = PushNotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """사용자의 알림 전체 읽음 처리"""
        PushNotification.objects.filter(user=request.user).update(is_read=True)
        return Response({"message": "사용자의 알림이 모두 읽음 처리되었습니다."}, status=status.HTTP_200_OK)

    def delete(self, request):
        """사용자의 알림 전체 삭제"""
        PushNotification.objects.filter(user=request.user).delete()
        return Response({"message": "사용자의 알림이 모두 삭제되었습니다."}, status=status.HTTP_200_OK)


@NotificationSchema.notification_settings_schema_view
class NotificationSettingsAPIView(APIView):
    """
    알림 설정 관리 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """알림 설정 조회"""
        settings = NotificationSettings.objects.get(user=request.user)
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """알림 설정 수정"""
        settings = NotificationSettings.objects.get(user=request.user)
        serializer = NotificationSettingsSerializer(settings, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
