from celery import shared_task
from celery.utils.log import get_task_logger

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

        logger.info(f"{log_prefix} 댓글({comment_id}) 알림 전송 시작")

        if comment.post:
            notification_service.send_notification_comment(Topic.POST, comment)
        elif comment.tasted_record:
            notification_service.send_notification_comment(Topic.TASTED_RECORD, comment)

        logger.info(f"{log_prefix} 댓글({comment_id}) 알림 전송 완료")
        return {"status": "success", "comment_id": comment_id, "task_id": task_id}

    except Comment.DoesNotExist:
        logger.error(f"{log_prefix} 댓글({comment_id})을 찾을 수 없습니다")
        return {"status": "error", "message": "댓글을 찾을 수 없습니다", "task_id": task_id}

    except Exception as e:
        logger.error(f"{log_prefix} 댓글({comment_id}) 알림 전송 실패: {str(e)}")
        self.retry(exc=e)
        return {"status": "retrying", "message": str(e), "task_id": task_id}
