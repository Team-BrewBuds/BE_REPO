import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from repo.interactions.relationship.models import Relationship
from repo.notifications.enums import Topic
from repo.notifications.services import NotificationService
from repo.profiles.models import CustomUser
from repo.records.models import Comment

logger = logging.getLogger(__name__)


# @receiver(post_save, sender=Post)
# def subscribe_post_topic(sender, instance: Post, created: bool, **kwargs):
#     """
#     게시글 생성 시 토픽 구독
#     """
#     if not created or settings.DEBUG:
#         return

#     notification_service = NotificationService()
#     topic = Topic.POST.topic_id(instance.id)
#     token = notification_service.get_device_token(instance.author)

#     if token:
#         notification_service.subscribe_topic(topic, token)
#         logger.info(f"게시글 {instance.id} 토픽 구독 완료")


# @receiver(post_save, sender=TastedRecord)
# def subscribe_tasted_record_topic(sender, instance: TastedRecord, created: bool, **kwargs):
#     """
#     시음기록 생성 시 토픽 구독
#     """
#     if not created or settings.DEBUG:
#         return

#     notification_service = NotificationService()
#     topic = Topic.TASTED_RECORD.topic_id(instance.id)
#     token = notification_service.get_device_token(instance.author)

#     if token:
#         notification_service.subscribe_topic(topic, token)
#         logger.info(f"시음기록 {instance.id} 토픽 구독 완료")


# @receiver(post_delete, sender=Post)
# def unsubscribe_post_topic(sender, instance: Post, **kwargs):
#     """
#     게시글 삭제 시 게시글, 댓글 작성자들의 토픽 구독 해제
#     """
#     if settings.DEBUG:
#         return

#     notification_service = NotificationService()
#     topic = Topic.POST.topic_id(instance.id)

#     unsubscribe_user_ids = set([instance.author.id])

#     comment_author_ids = instance.comments.exclude(author=instance.author).values_list("author_id", flat=True).distinct()
#     unsubscribe_user_ids.update(comment_author_ids)

#     tokens = notification_service.get_device_tokens(list(unsubscribe_user_ids))

#     fcm_service = FCMService()
#     fcm_service.unsubscribe_topic(topic, tokens)
#     logger.info(f"게시글 {instance.id}의 모든 구독자({len(tokens)}명) 토픽 해지 완료")


# @receiver(post_delete, sender=TastedRecord)
# def unsubscribe_tasted_record_topic(sender, instance: TastedRecord, **kwargs):
#     """
#     시음기록 삭제 시 게시글, 댓글 작성자들의 토픽 구독 해제
#     """
#     if settings.DEBUG:
#         return

#     notification_service = NotificationService()
#     topic = Topic.TASTED_RECORD.topic_id(instance.id)

#     unsubscribe_user_ids = set([instance.author.id])

#     comment_author_ids = instance.comments.exclude(author=instance.author).values_list("author_id", flat=True).distinct()
#     unsubscribe_user_ids.update(comment_author_ids)

#     tokens = notification_service.get_device_tokens(list(unsubscribe_user_ids))

#     fcm_service = FCMService()
#     fcm_service.unsubscribe_topic(topic, tokens)
#     logger.info(f"시음기록 {instance.id}의 모든 구독자({len(tokens)}명) 토픽 해지 완료")


@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance: Comment, created: bool, **kwargs):
    """
    댓글 생성 시 Celery task를 통해 알림 전송
    """
    if not created:
        return

    try:
        comment = Comment.objects.get(id=instance.id)

        notification_service = NotificationService()
        if comment.post:
            is_sent = notification_service.send_notification_comment(Topic.POST, comment.post, comment)
        elif comment.tasted_record:
            is_sent = notification_service.send_notification_comment(Topic.TASTED_RECORD, comment.tasted_record, comment)

        if not is_sent:
            return

        logger.info(f"댓글({comment.id}) 알림 전송 완료")
        return {"status": "success", "comment_id": comment.id}

    except Comment.DoesNotExist:
        logger.error(f"댓글({comment.id})을 찾을 수 없습니다")
        return {"status": "error", "message": "댓글을 찾을 수 없습니다"}

    except Exception as e:
        logger.error(f"댓글({comment.id}) 알림 전송 실패: {str(e)}")
        return {"status": "retrying", "message": str(e)}


@receiver(post_save, sender=Relationship)
def send_follow_notification(sender, instance: Relationship, created: bool, **kwargs):
    """
    팔로우 생성 시 알림 전송 및 저장
    """

    if not created or instance.relationship_type != "follow":
        return

    try:
        follower = CustomUser.objects.get(id=instance.from_user.id)
        followee = CustomUser.objects.get(id=instance.to_user.id)

        notification_service = NotificationService()
        is_sent = notification_service.send_notification_follow(follower, followee)

        if not is_sent:
            return

        logger.info(f"팔로우({instance.id}) 알림 전송 완료")
        return {"status": "success", "follower_id": follower.id, "followee_id": followee.id}

    except CustomUser.DoesNotExist:
        logger.error(f"팔로우({instance.id}) 알림 전송 실패: 사용자를 찾을 수 없습니다")
        return {"status": "error", "message": "사용자를 찾을 수 없습니다"}

    except Exception as e:
        logger.error(f"팔로우({instance.id}) 알림 전송 실패: {str(e)}")
        return {"status": "retrying", "message": str(e)}
