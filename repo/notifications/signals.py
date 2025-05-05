import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from repo.interactions.relationship.models import Relationship
from repo.records.models import Comment

from .tasks import send_notification_comment, send_notification_follow

logger = logging.getLogger("django.server")


@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance: Comment, created: bool, **kwargs):
    """
    댓글 생성 시 Celery task를 통해 알림 전송
    """
    if not created:
        return

    try:
        send_notification_comment.delay(instance.id)
    except Exception as e:
        logger.error(f"댓글 알림 task 등록 실패: {str(e)}")


@receiver(post_save, sender=Relationship)
def send_follow_notification(sender, instance: Relationship, created: bool, **kwargs):
    """
    팔로우 생성 시 알림 전송 및 저장
    """

    if not created or instance.relationship_type != "follow":
        return

    try:
        send_notification_follow.delay(instance.from_user.id, instance.to_user.id)
    except Exception as e:
        logger.error(f"팔로우 알림 전송 실패: {str(e)}")
