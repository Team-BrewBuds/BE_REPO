import firebase_admin
from django.conf import settings
from django.utils.log import get_logger
from firebase_admin import credentials, exceptions, messaging
from firebase_admin.messaging import Message, MulticastMessage, Notification

from repo.notifications.enums import Topic
from repo.notifications.models import NotificationSettings, UserDevice
from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord

logger = get_logger(__name__)

SERVICE_ACCOUNT_FILE = getattr(settings, "FCM_SERVICE_ACCOUNT_FILE", None)
PROJECT_ID = getattr(settings, "FCM_PROJECT_ID", None)


class FCMService:
    """
    FCM 알림 서비스
    """

    cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)

    def __init__(self):
        firebase_admin.initialize_app(self.cred)

    def send_push_notification_to_single_device(self, device_token: str, title: str, body: str, data: dict = None):
        """
        단일 디바이스에 알림 전송
        """
        message = Message(
            notification=Notification(title=title, body=body),
            token=device_token,
            data=data if data else None,
        )

        response = messaging.send(message, dry_run=True)
        logger.info(f"Successfully sent single message: {response}")

    def send_push_notification_to_multiple_devices(self, device_tokens: list[str], title: str, body: str, data: dict = None):
        """
        여러 디바이스에 알림 전송
        """
        message = MulticastMessage(notification=Notification(title=title, body=body), tokens=device_tokens, data=data if data else None)

        response = messaging.send_multicast(message)
        logger.info(f"Successfully sent multiple message: {response}")

    def send_push_notification_silent(self, device_token: str, data: dict):
        """
        단일 디바이스에 무음 알림 전송
        """
        message = Message(token=device_token, data=data)

        response = messaging.send(message)
        logger.info(f"Successfully sent silent message: {response}")

    def send_push_notification_to_topic(self, topic: str, title: str, body: str, data: dict = None):
        """
        토픽에 알림 전송
        """

        message = Message(notification=Notification(title=title, body=body), topic=topic, data=data if data else None)

        response = messaging.send(message)
        logger.info(f"Successfully sent topic message: {response}")

    def subscribe_topic(self, topic: str, token: str):
        """
        토픽 설정
        """
        try:
            messaging.subscribe_to_topic(token, topic)
        except ValueError as e:
            logger.error(f"Failed to subscribe to topic: {e}")
        except exceptions.FirebaseError as e:
            logger.error(f"Failed to subscribe to topic: {e}")

    def unsubscribe_topic(self, topic: str, token: str):
        """
        토픽 해지
        """
        try:
            messaging.unsubscribe_from_topic(token, topic)
        except ValueError as e:
            logger.error(f"Failed to unsubscribe from topic: {e}")
        except exceptions.FirebaseError as e:
            logger.error(f"Failed to unsubscribe from topic: {e}")


class NotificationService:
    """
    알림 서비스
    """

    def __init__(self):
        self.fcm_service = FCMService()

    def can_send_notification(self, user: CustomUser, notification_type: str) -> bool:
        """
        알림 전송 가능 여부 확인
        """
        return all([self.check_notification_settings(user, notification_type), self.get_device_token(user)])

    def check_notification_settings(self, user: CustomUser, notification_type: str) -> bool:
        """
        알림 설정 확인
        """
        notification_settings = NotificationSettings.objects.filter(user=user).first()
        return getattr(notification_settings, notification_type)

    def get_device_token(self, user: CustomUser) -> str | None:
        """
        사용자의 디바이스 토큰 조회
        """
        device_token = UserDevice.objects.filter(user=user, is_active=True).first()
        return device_token.device_token if device_token else None

    def send_notification_comment(self, topic: Topic, comment: Comment):
        """
        토픽 구독 알림 전송
        title : 댓글 작성자 닉네임
        body : 댓글 내용
        topic : 해당 게시물의 topic id
        """
        if isinstance(comment.post, Post):
            target_object = comment.post
        else:
            target_object = comment.tasted_record

        comment_author = comment.author.nickname
        comment_content = comment.content[:20]  # 댓글 내용 20자 제한
        target_object_id = target_object.id
        topic_id = topic.get_topic_id(target_object_id)

        self.fcm_service.send_push_notification_to_topic(
            title=comment_author,
            body=comment_content,
            data={"comment_id": comment.id},
            topic=topic_id,
        )

    def send_notification_like(self, object_type: Post | TastedRecord | Comment, liked_user: CustomUser):
        """
        게시물 좋아요 알림 전송
        title : 브루버즈
        body : {좋아요 누른 사용자 닉네임}님이 버디님의 게시물을 좋아해요.
        token : 게시물 작성자의 token
        """
        if isinstance(object_type, Post):
            object_str = "게시물"
        elif isinstance(object_type, TastedRecord):
            object_str = "시음 기록"
        else:
            object_str = "댓글"

        device_token = self.get_device_token(object_type.author)

        self.fcm_service.send_push_notification_to_single_device(
            title="브루버즈",
            body=f"{liked_user.nickname}님이 버디님의 {object_str}을 좋아해요.",
            data={"object_id": object_type.id},
            device_token=device_token,
        )

    def send_notification_follow(self, follower: CustomUser, followee: CustomUser):
        """
        팔로우 알림 전송
        title : 브루버즈
        body : {팔로우 신청한 사용자의 닉네임}님이 버디님을 팔로우하기 시작했어요.
        token : 팔로우 당한 사용자의 token
        """
        device_token = self.get_device_token(followee)

        self.fcm_service.send_push_notification_to_single_device(
            title="브루버즈",
            body=f"{follower.nickname}님이 버디님을 팔로우하기 시작했어요.",
            data={"following_user_id": follower.id},
            device_token=device_token,
        )
