from rest_framework import serializers

from .models import NotificationSetting, PushNotification, UserDevice


class PushNotificationSerializer(serializers.ModelSerializer):
    """
    푸시 알림 시리얼라이저
    """

    class Meta:
        model = PushNotification
        fields = ["id", "notification_type", "title", "body", "data", "is_read", "created_at"]


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """
    알림 설정 시리얼라이저
    """

    class Meta:
        model = NotificationSetting
        fields = ["like_notify", "comment_notify", "follow_notify", "marketing_notify"]


class UserDeviceSerializer(serializers.ModelSerializer):
    """
    사용자 디바이스 정보 시리얼라이저
    """

    class Meta:
        model = UserDevice
        fields = ["device_token", "device_type"]
