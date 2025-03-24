import logging
import time
from typing import List, Optional

import firebase_admin
from django.conf import settings
from django.db import transaction
from firebase_admin import credentials, exceptions, messaging
from firebase_admin.messaging import Message, MulticastMessage, Notification

from repo.notifications.enums import Topic
from repo.notifications.models import NotificationSetting, PushNotification, UserDevice
from repo.notifications.templates import NotificationTemplate
from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord

logger = logging.getLogger("django.server")

SERVICE_ACCOUNT_FILE = getattr(settings, "FCM_SERVICE_ACCOUNT_FILE", None)
DRY_RUN = True if settings.DEBUG else False


class FCMService:
    """
    FCM 알림 서비스
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            try:
                cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
                self.app = firebase_admin.initialize_app(cred)
            except (ValueError, FileNotFoundError) as e:
                logger.error(f"Firebase 초기화 실패: {str(e)}")
                if not settings.DEBUG:
                    raise
            except Exception as e:
                logger.error(f"Firebase 초기화 중 예상치 못한 오류 발생: {str(e)}")
                raise
            self._initialized = True

    def send_push_notification_to_single_device(self, device_token: str, title: str, body: str, data: dict = None) -> bool:
        """
        단일 디바이스에 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_token:
            logger.warning("디바이스 토큰이 없습니다.")
            return False

        def send():
            message = Message(
                notification=Notification(title=title, body=body),
                token=device_token,
                data=data or {},
            )
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent single message: {response}")
            return True

        try:
            return self._retry_send(send)
        except exceptions.UnauthenticatedError as e:
            self._handle_invalid_token(device_token)
            return False
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {str(e)}")
            return False

    def send_push_notification_to_multiple_devices(self, device_tokens: List[str], title: str, body: str, data: dict = None) -> bool:
        """
        여러 디바이스에 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_tokens:
            logger.warning("전송할 디바이스 토큰이 없습니다.")
            return False

        def send():
            notification = Notification(title=title, body=body)
            message = MulticastMessage(notification, tokens=device_tokens, data=data or {})
            response: messaging.BatchResponse = messaging.send_each_for_multicast(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent multiple message: {response}")

            if response.failure_count > 0:
                self._handle_failed_tokens(device_tokens, response)

            return response.success_count > 0

        try:
            return self._retry_send(send)
        except Exception as e:
            logger.error(f"다중 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @staticmethod
    def _handle_invalid_token(device_token: str) -> None:
        """무효한 토큰 처리"""
        with transaction.atomic():
            UserDevice.objects.filter(device_token=device_token).delete()
            logger.info(f"Removed invalid token: {device_token}")

    def _handle_failed_tokens(self, device_tokens: List[str], response: messaging.BatchResponse) -> None:
        """실패한 토큰들 처리"""
        failed_tokens = [device_tokens[idx] for idx, resp in enumerate(response.responses) if not resp.success]
        if failed_tokens:
            with transaction.atomic():
                UserDevice.objects.filter(device_token__in=failed_tokens).delete()
                logger.info(f"Removed {len(failed_tokens)} invalid tokens")

    def send_push_notification_silent(self, device_token: str, data: dict = None) -> bool:
        """
        단일 디바이스에 무음 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_token:
            logger.warning("디바이스 토큰이 없습니다.")
            return False

        def send():
            message = Message(token=device_token, data=data or {})
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent silent message: {response}")
            return True

        try:
            return self._retry_send(send)
        except exceptions.UnauthenticatedError as e:
            self._handle_invalid_token(device_token)
            return False
        except Exception as e:
            logger.error(f"무음 메시지 전송 중 오류 발생: {str(e)}")
            return False

    def send_push_notification_to_topic(self, topic: str, title: str, body: str, data: dict = None) -> bool:
        """
        토픽에 알림 전송
        Args:
            topic: 토픽 식별자
            title: 알림 제목
            body: 알림 내용
            data: 추가 데이터
        Returns:
            bool: 전송 성공 여부
        """
        if not topic:
            logger.warning("토픽이 지정되지 않았습니다.")
            return False

        def send():
            notification = Notification(title=title, body=body)
            message = Message(notification=notification, topic=topic, data=data or {})
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent topic message: {response}")
            return True

        try:
            return self._retry_send(send)
        except Exception as e:
            logger.error(f"토픽 메시지 전송 중 오류 발생: {str(e)}")
            return False

    def subscribe_topic(self, topic: str, token: str) -> bool:
        """
        토픽 구독 설정
        Args:
            topic: 구독할 토픽
            token: 디바이스 토큰
        Returns:
            bool: 구독 성공 여부
        """
        if not all([topic, token]):
            logger.warning("토픽 또는 토큰이 지정되지 않았습니다.")
            return False

        def subscribe():
            messaging.subscribe_to_topic(token, topic)
            logger.info(f"Successfully subscribed to topic: {topic}")
            return True

        try:
            return self._retry_send(subscribe)
        except (ValueError, exceptions.FirebaseError) as e:
            logger.error(f"토픽 구독 실패: {str(e)}")
            return False

    def unsubscribe_topic(self, topic: str, token: str) -> bool:
        """
        토픽 구독 해지
        Args:
            topic: 해지할 토픽
            token: 디바이스 토큰
        Returns:
            bool: 해지 성공 여부
        """
        if not all([topic, token]):
            logger.warning("토픽 또는 토큰이 지정되지 않았습니다.")
            return False

        def unsubscribe():
            messaging.unsubscribe_from_topic(token, topic)
            logger.info(f"Successfully unsubscribed from topic: {topic}")
            return True

        try:
            return self._retry_send(unsubscribe)
        except (ValueError, exceptions.FirebaseError) as e:
            logger.error(f"토픽 구독 해지 실패: {str(e)}")
            return False

    def _retry_send(self, func, *args, max_retries=3):
        for attempt in range(max_retries):
            try:
                return func(*args)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2**attempt)


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
        if not user:
            return False

        can_send_noti = self.check_notification_settings(user, notification_type)
        device_token = self.get_device_token(user)

        return bool(can_send_noti and device_token)

    @staticmethod
    def check_notification_settings(user: CustomUser, notification_type: str) -> bool:
        """
        알림 설정 확인
        """
        try:
            notification_settings = NotificationSetting.objects.get(user=user)
            return getattr(notification_settings, notification_type, False)
        except NotificationSetting.DoesNotExist:
            return False

    @staticmethod
    def get_device_token(user: CustomUser) -> Optional[str]:
        """
        사용자의 디바이스 토큰 조회
        """
        device = UserDevice.objects.filter(user=user, is_active=True).select_related("user").first()
        return device.device_token if device else None

    def send_notification_comment(self, topic: Topic, comment: Comment):
        """
        댓글 알림 전송
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
        message = NotificationTemplate(comment_author).comment_noti_template(comment_content)
        data = {"comment_id": comment.id}
        topic_id = topic.get_topic_id(target_object.id)

        self.fcm_service.send_push_notification_to_topic(
            title=message["title"],
            body=message["body"],
            data=data,
            topic=topic_id,
        )

        self.save_push_notification(comment.author, "comment", message["title"], message["body"], data)

    def send_notification_like(self, object_type: Post | TastedRecord | Comment, liked_user: CustomUser):
        """
        게시물 좋아요 알림 전송
        title : 브루버즈
        body : {좋아요 누른 사용자 닉네임}님이 버디님의 게시물을 좋아해요.
        token : 게시물 작성자의 token
        """

        author = object_type.author
        if not self.check_notification_settings(author, "like_notify"):
            return

        if isinstance(object_type, Post):
            object_str = "게시물"
        elif isinstance(object_type, TastedRecord):
            object_str = "시음 기록"
        else:
            object_str = "댓글"

        message = NotificationTemplate(liked_user.nickname).like_noti_template(object_str)
        data = {"object_id": object_type.id}
        device_token = self.get_device_token(author)

        self.fcm_service.send_push_notification_to_single_device(
            title=message["title"],
            body=message["body"],
            data=data,
            device_token=device_token,
        )

        self.save_push_notification(author, "like", message["title"], message["body"], data)

    def send_notification_follow(self, follower: CustomUser, followee: CustomUser):
        """
        팔로우 알림 전송
        title : 브루버즈
        body : {팔로우 신청한 사용자의 닉네임}님이 버디님을 팔로우하기 시작했어요.
        token : 팔로우 당한 사용자의 token
        """
        if not self.check_notification_settings(followee, "follow_notify"):
            return

        message = NotificationTemplate(follower.nickname).follow_noti_template()
        data = {"following_user_id": follower.id}
        device_token = self.get_device_token(followee)

        self.fcm_service.send_push_notification_to_single_device(
            title=message["title"],
            body=message["body"],
            data=data,
            device_token=device_token,
        )

        self.save_push_notification(followee, "follow", message["title"], message["body"], data)

    def save_push_notification(self, user: CustomUser, notification_type: str, title: str, body: str, data: dict):
        """
        푸시 알림 저장
        """

        try:
            device = UserDevice.objects.get(user=user)
            PushNotification.objects.create(device=device, notification_type=notification_type, title=title, body=body, data=data)
        except UserDevice.DoesNotExist:
            logger.error(f"사용자 {user.id}의 디바이스를 찾을 수 없습니다.")
        except Exception as e:
            logger.error(f"알림 저장 중 오류 발생: {str(e)}")
