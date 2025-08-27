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

    def validate_device_token(self, value: str) -> str:
        """디바이스 토큰 유효성 검사"""
        if not value:
            raise serializers.ValidationError("디바이스 토큰은 필수 입력 항목입니다.")

        if value.lower() not in [device_type[0] for device_type in UserDevice.DEVICE_TYPE_CHOICES]:
            raise serializers.ValidationError("유효하지 않은 디바이스 토큰입니다.")

        return value

    class Meta:
        model = UserDevice
        fields = ["device_token", "device_type"]


class NotificationTestSerializer(serializers.Serializer):
    """
    푸시 알림 테스트용 시리얼라이저
    """

    device_token = serializers.ListField(child=serializers.CharField(), required=True)
