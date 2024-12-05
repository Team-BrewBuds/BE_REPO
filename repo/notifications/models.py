from django.db import models

from repo.profiles.models import CustomUser

# TODO : migration


class UserDevice(models.Model):
    DEVICE_TYPE_CHOICES = [
        ("ios", "iOS"),
        ("android", "Android"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    device_token = models.CharField(max_length=255)
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "device_token")
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["device_token"]),
        ]


class PushNotification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        # ('new_post', '새 게시물'),
        # ("new_tasted_record", "새 시음 기록"),
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


class NotificationSettings(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    new_post_notify = models.BooleanField(default=True)
    like_notify = models.BooleanField(default=True)
    comment_notify = models.BooleanField(default=True)
    marketing_notify = models.BooleanField(default=False)
