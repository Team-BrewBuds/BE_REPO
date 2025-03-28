from django.db import models

from repo.profiles.models import CustomUser


class UserDevice(models.Model):
    """
    사용자 디바이스 정보
    """

    DEVICE_TYPE_CHOICES = [
        ("ios", "iOS"),
        ("android", "Android"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    device_token = models.CharField(max_length=255)
    device_type = models.CharField(max_length=10, default="ios", choices=DEVICE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "device_token", "device_type")
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["device_token"]),
        ]


class PushNotification(models.Model):
    """
    푸시 알림 기록
    """

    NOTIFICATION_TYPE_CHOICES = [
        ("new_comment", "새 댓글"),
        ("like", "좋아요"),
        ("follow", "팔로우"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    data = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class NotificationSetting(models.Model):
    """
    사용자별 알림 설정
    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    like_notify = models.BooleanField(default=True)
    comment_notify = models.BooleanField(default=True)
    follow_notify = models.BooleanField(default=True)
    marketing_notify = models.BooleanField(default=False)
