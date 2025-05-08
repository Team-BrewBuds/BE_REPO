import logging
import os
from datetime import timedelta
from typing import Dict, List, Optional

import firebase_admin
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from firebase_admin import credentials, exceptions, messaging
from firebase_admin.messaging import Message, MulticastMessage, Notification

from repo.common.decorators import retry
from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord

from .enums import Topic
from .message_templates import PushNotificationRecordTemplate, PushNotificationTemplate
from .models import NotificationSetting, PushNotification, UserDevice

logger = logging.getLogger("django.server")

SERVICE_ACCOUNT_FILE = getattr(settings, "FCM_SERVICE_ACCOUNT_FILE", None)
DRY_RUN = True if settings.DEBUG else False


class FCMService:
    """FCM 알림 서비스"""

    def __init__(self):
        self._initialize_firebase()

    def _initialize_firebase(self):
        """Firebase Admin SDK 초기화"""
        if not SERVICE_ACCOUNT_FILE:
            raise ValueError("FCM_SERVICE_ACCOUNT_FILE 설정이 없습니다.")

        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(f"Firebase 서비스 계정 키 파일을 찾을 수 없습니다: {SERVICE_ACCOUNT_FILE}")

        try:
            self.app = self._get_or_create_firebase_app()
            logger.info("Firebase 초기화 성공")
        except Exception as e:
            self._handle_initialization_error(e)

    def _get_or_create_firebase_app(self):
        """기존 Firebase 앱을 가져오거나 새로 생성"""
        try:
            return firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
            return firebase_admin.initialize_app(cred)

    def _handle_initialization_error(self, error):
        """초기화 에러 처리"""
        logger.error(f"Firebase 초기화 중 오류 발생: {str(error)}")
        if settings.DEBUG:
            logger.warning("개발 환경: Firebase 초기화를 건너뜁니다.")
        else:
            raise

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

    @retry(max_retries=3)
    def send_push_notification_to_single_device(self, device_token: str, title: str, body: str, data: dict = None) -> bool:
        """
        단일 디바이스에 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_token:
            logger.warning("디바이스 토큰이 없습니다.")
            return False

        try:
            message = Message(
                notification=Notification(title=title, body=body),
                token=device_token,
                data=data or {},
            )
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent single message: {response}")
            return True
        except exceptions.UnauthenticatedError as e:
            self._handle_invalid_token(device_token)
            return False
        except Exception as e:
            logger.error(f"메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
    def send_push_notification_to_multiple_devices(self, device_tokens: List[str], title: str, body: str, data: dict = None) -> bool:
        """
        여러 디바이스에 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_tokens:
            logger.warning("전송할 디바이스 토큰이 없습니다.")
            return False

        try:
            notification = Notification(title=title, body=body)
            message = MulticastMessage(tokens=device_tokens, data=data or {}, notification=notification)
            response: messaging.BatchResponse = messaging.send_each_for_multicast(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent multiple message: {response}")

            if response.failure_count > 0:
                self._handle_failed_tokens(device_tokens, response)

            return response.success_count > 0
        except Exception as e:
            logger.error(f"다중 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
    def send_push_notification_silent(self, device_token: str, data: dict = None) -> bool:
        """
        단일 디바이스에 무음 알림 전송
        Returns:
            bool: 전송 성공 여부
        """
        if not device_token:
            logger.warning("디바이스 토큰이 없습니다.")
            return False

        try:
            message = Message(token=device_token, data=data or {})
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent silent message: {response}")
            return True
        except exceptions.UnauthenticatedError as e:
            self._handle_invalid_token(device_token)
            return False
        except Exception as e:
            logger.error(f"무음 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
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

        try:
            notification = Notification(title=title, body=body)
            message = Message(data=data or {}, notification=notification, topic=topic)
            response = messaging.send(message, dry_run=DRY_RUN)
            logger.info(f"Successfully sent topic message: {response}")
            return True
        except Exception as e:
            logger.error(f"토픽 메시지 전송 중 오류 발생: {str(e)}")
            return False

    @retry(max_retries=3)
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

        try:
            messaging.subscribe_to_topic(token, topic)
            logger.info(f"Successfully subscribed to topic: {topic}")
            return True
        except (ValueError, exceptions.FirebaseError) as e:
            logger.error(f"토픽 구독 실패: {str(e)}")
            return False

    @retry(max_retries=3)
    def unsubscribe_topic(self, topic: str, tokens: List[str]) -> bool:
        """
        토픽 구독 해지
        Args:
            topic: 해지할 토픽
            token: 디바이스 토큰
        Returns:
            bool: 해지 성공 여부
        """
        if not all([topic, tokens]):
            logger.warning("토픽 또는 토큰이 지정되지 않았습니다.")
            return False

        try:
            messaging.unsubscribe_from_topic(tokens, topic)
            logger.info(f"Successfully unsubscribed from topic: {topic}")
            return True
        except (ValueError, exceptions.FirebaseError) as e:
            logger.error(f"토픽 구독 해지 실패: {str(e)}")
            return False


class NotificationService:
    """
    알림 서비스
    """

    def __init__(self):
        self.fcm_service = FCMService()

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
    def check_duplicate_notification(user: CustomUser, notification_type: str, data: dict, minutes: int = 5) -> bool:
        """
        일정 시간 내 중복 알림 체크
        Args:
            user: 알림 대상 사용자
            notification_type: 알림 타입
            data: 대상 객체 데이터
            minutes: 중복 체크 시간 (분)
        Returns:
            bool: 중복 알림이 있으면 True, 없으면 False
        """

        recent_notification = PushNotification.objects.filter(
            user=user, notification_type=notification_type, data=data, created_at__gte=timezone.now() - timedelta(minutes=minutes)
        ).first()

        return bool(recent_notification)

    @staticmethod
    def get_device_token(user: CustomUser) -> Optional[str]:
        """
        사용자의 디바이스 토큰 조회
        """
        device = UserDevice.objects.filter(user=user, is_active=True).first()
        return device.device_token if device else None

    @staticmethod
    def get_device_tokens(user_ids: List[int]) -> List[str]:
        """
        사용자들의 디바이스 토큰 조회
        """
        tokens = UserDevice.objects.filter(user_id__in=user_ids, is_active=True).values_list("device_token", flat=True)
        return list(tokens)

    @transaction.atomic
    def send_notification_comment(self, topic: Topic, target_object: Post | TastedRecord, comment: Comment) -> None:
        """
        댓글 알림 전송

        알림 대상 선정
        - {알림 대상} - {알림 트리거 유저} - {댓글 알림 설정 OFF 유저}
        - 댓글 작성시 : 댓글의 해당 게시물 작성자만 고려
        - 대댓글 작성시 : 대댓글의 해당 댓글의 작성자만 고려
        """

        comment_author = comment.author

        if reply := comment.parent:  # 대댓글인 경우
            noti_target_user = reply.author
            comment_noti_msg = PushNotificationTemplate(comment_author.nickname).comment_noti_template(is_reply=True)
        else:  # 댓글인 경우
            noti_target_user = target_object.author
            comment_noti_msg = PushNotificationTemplate(comment_author.nickname).comment_noti_template(
                is_reply=False, object_type=topic.display_name
            )

        data = {
            "comment_id": str(comment.id),
            "object_id": str(target_object.id),
            "object_type": topic.display_name,
        }

        if noti_target_user.id == comment_author.id:
            return  # 댓글 작성자와 대상 객체 작성자가 같은 경우 알림 전송 제외

        has_comment_notify = NotificationSetting.objects.filter(user=noti_target_user).values_list("comment_notify", flat=True).first()
        if not has_comment_notify:
            return  # 댓글 알림 설정 OFF 유저

        device_token = self.get_device_token(noti_target_user)
        if not device_token:
            return  # 댓글 알림 설정 ON 유저이지만 디바이스 토큰이 없는 경우 알림 전송 제외

        self.fcm_service.send_push_notification_to_single_device(
            device_token=device_token,
            title=comment_noti_msg["title"],
            body=comment_noti_msg["body"],
            data=data,
        )
        logger.info(f"댓글 알림 전송 완료 - comment_id: {comment.id}, target_user: {noti_target_user.id}")

        self.save_push_notification_comment(comment, noti_target_user, data, comment_noti_msg)

    def send_notification_like(self, liked_obj: Post | TastedRecord | Comment, liked_user: CustomUser) -> None:
        """
        게시물 좋아요 알림 전송
        - 제외 조건: 자신의 게시물에 좋아요를 누른 경우, 댓글 좋아요, 좋아요 알림 설정 OFF
        """

        liked_obj_author = liked_obj.author
        if any(
            [
                liked_obj_author.id == liked_user.id,
                isinstance(liked_obj, Comment),
                not self.check_notification_settings(liked_obj_author, "like_notify"),
            ]
        ):
            return

        object_type_map = {Post: ("게시물", "post_id"), TastedRecord: ("시음 기록", "tasted_record_id")}

        object_str, id_key = object_type_map[type(liked_obj)]
        data = {id_key: str(liked_obj.id)}

        message = PushNotificationTemplate(liked_user.nickname).like_noti_template(object_str)
        device_token = self.get_device_token(liked_obj_author)

        self.fcm_service.send_push_notification_to_single_device(
            title=message["title"],
            body=message["body"],
            data=data,
            device_token=device_token,
        )
        logger.info(f"좋아요 알림 전송 완료 - liked_obj_id: {liked_obj.id}, liked_user: {liked_user.id}")

        self.save_push_notification_like(liked_obj, liked_user, data, object_str)

    def send_notification_follow(self, follower: CustomUser, followee: CustomUser) -> None:
        """
        팔로우 알림 전송
        """
        if not self.check_notification_settings(followee, "follow_notify"):
            return

        message = PushNotificationTemplate(follower.nickname).follow_noti_template()
        data = {"follower_user_id": str(follower.id)}
        device_token = self.get_device_token(followee)

        self.fcm_service.send_push_notification_to_single_device(
            title=message["title"],
            body=message["body"],
            data=data,
            device_token=device_token,
        )

        logger.info(f"팔로우 알림 전송 완료 - follower: {follower.id}, followee: {followee.id}")

        self.save_push_notification_follow(follower, followee)

    # 알림 저장 메서드

    def save_push_notification_comment(self, comment: Comment, noti_target_user: CustomUser, data: dict, comment_noti_msg: Dict[str, str]):
        """
        댓글 알림 저장
        """

        self.save_push_notification(noti_target_user, "comment", data, comment_noti_msg)

        logger.info(f"댓글 알림 저장 완료 - comment_id: {comment.id}, target_user: {noti_target_user.id}")

    def save_push_notification_like(self, liked_obj: Post | TastedRecord | Comment, liked_user: CustomUser, data: dict, object_str: str):
        """
        좋아요 알림 저장
        """

        liked_obj_author = liked_obj.author
        record_message = PushNotificationRecordTemplate(liked_user.nickname).like_noti_template(object_str)

        self.save_push_notification(liked_obj_author, "like", data, record_message)

        logger.info(f"좋아요 알림 저장 완료 - liked_obj_id: {liked_obj.id}, liked_user: {liked_user.id}")

    def save_push_notification_follow(self, follower: CustomUser, followee: CustomUser):
        """
        팔로우 알림 저장
        """

        record_message = PushNotificationRecordTemplate(follower.nickname).follow_noti_template()
        data = {"follower_user_id": str(follower.id)}

        self.save_push_notification(followee, "follow", data, record_message)

        logger.info(f"팔로우 알림 저장 완료 - follower: {follower.id}, followee: {followee.id}")

    def save_push_notification(self, user: CustomUser, notification_type: str, data: dict, record_message: Dict[str, str]):
        """
        푸시 알림 저장
        """

        PushNotification.objects.create(
            user=user,
            notification_type=notification_type,
            title=record_message["title"],
            body=record_message["body"],
            data=data,
        )

    def save_push_notifications(self, user_ids: List[int], notification_type: str, data: dict, record_message: Dict[str, str]):
        """
        푸시 알림들 저장
        """
        PushNotification.objects.bulk_create(
            [
                PushNotification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=record_message["title"],
                    body=record_message["body"],
                    data=data,
                )
                for user_id in user_ids
            ]
        )
