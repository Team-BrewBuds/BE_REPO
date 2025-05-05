from celery import shared_task
from celery.utils.log import get_task_logger

from repo.common.utils import get_object_by_type
from repo.profiles.models import CustomUser
from repo.records.models import Comment

from .enums import Topic
from .services import NotificationService

logger = get_task_logger(__name__)


@shared_task(name="repo.notifications.tasks.send_notification_comment", bind=True, default_retry_delay=10, max_retries=3)
def send_notification_comment(self, comment_id):
    """
    댓글 알림을 비동기적으로 전송하는 Celery task
    """
    task_id = self.request.id
    log_prefix = f"[Task {task_id}]"

    try:
        comment = Comment.objects.get(id=comment_id)

        notification_service = NotificationService()
        if comment.post:
            notification_service.send_notification_comment(Topic.POST, comment.post, comment)
        elif comment.tasted_record:
            notification_service.send_notification_comment(Topic.TASTED_RECORD, comment.tasted_record, comment)

        logger.info(f"{log_prefix} 댓글({comment_id}) 알림 전송 완료")
        return {"status": "success", "comment_id": comment_id, "task_id": task_id}

    except Comment.DoesNotExist:
        logger.error(f"{log_prefix} 댓글({comment_id})을 찾을 수 없습니다")
        return {"status": "error", "message": "댓글을 찾을 수 없습니다", "task_id": task_id}

    except Exception as e:
        logger.error(f"{log_prefix} 댓글({comment_id}) 알림 전송 실패: {str(e)}")
        self.retry(exc=e)
        return {"status": "retrying", "message": str(e), "task_id": task_id}


@shared_task(name="repo.notifications.tasks.send_notification_follow", bind=True, default_retry_delay=10, max_retries=3)
def send_notification_follow(self, follower_id, followee_id):
    """
    팔로우 알림을 비동기적으로 전송하는 Celery task
    """
    task_id = self.request.id
    log_prefix = f"[Task {task_id}]"

    try:
        follower = CustomUser.objects.get(id=follower_id)
        followee = CustomUser.objects.get(id=followee_id)

        notification_service = NotificationService()
        notification_service.send_notification_follow(follower, followee)

        logger.info(f"{log_prefix} 팔로우 알림 전송 완료")
        return {"status": "success", "follower_id": follower.id, "followee_id": followee.id, "task_id": task_id}

    except CustomUser.DoesNotExist:
        logger.error(f"{log_prefix} 팔로우 알림 전송 실패: 사용자를 찾을 수 없습니다")
        return {"status": "error", "message": "사용자를 찾을 수 없습니다", "task_id": task_id}

    except Exception as e:
        logger.error(f"{log_prefix} 팔로우 알림 전송 실패: {str(e)}")
        self.retry(exc=e)
        return {"status": "retrying", "message": str(e), "task_id": task_id}


@shared_task(name="repo.notifications.tasks.send_notification_like", bind=True, default_retry_delay=10, max_retries=3)
def send_notification_like(self, liked_obj_type, liked_obj_id, liked_user_id):
    """
    좋아요 알림을 비동기적으로 전송하는 Celery task
    """
    task_id = self.request.id
    log_prefix = f"[Task {task_id}]"

    try:
        liked_user = CustomUser.objects.get(id=liked_user_id)
        liked_obj = get_object_by_type(liked_obj_type, liked_obj_id)

        notification_service = NotificationService()
        notification_service.send_notification_like(liked_obj, liked_user)

        logger.info(f"{log_prefix} 좋아요 알림 전송 완료")
        return {
            "status": "success",
            "liked_obj_type": liked_obj_type,
            "liked_obj_id": liked_obj_id,
            "liked_user_id": liked_user_id,
            "task_id": task_id,
        }

    except CustomUser.DoesNotExist:
        logger.error(f"{log_prefix} 좋아요 알림 전송 실패: 사용자를 찾을 수 없습니다")
        return {"status": "error", "message": "사용자를 찾을 수 없습니다", "task_id": task_id}

    except Exception as e:
        logger.error(f"{log_prefix} 좋아요 알림 전송 실패: {str(e)}")
        self.retry(exc=e)
        return {"status": "retrying", "message": str(e), "task_id": task_id}
