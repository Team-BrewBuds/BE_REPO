from rest_framework import serializers

from .models import NotificationSettings, PushNotification


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
        model = NotificationSettings
        fields = ["like_notify", "comment_notify", "follow_notify", "marketing_notify"]
