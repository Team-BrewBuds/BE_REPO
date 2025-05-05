import logging
from typing import Dict, List, Optional

from django.db import transaction

from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord

from .enums import Topic
from .fcm import FCMService
from .message_templates import (
    PushNotificationRecordTemplate,
    PushNotificationTemplate,
)
from .models import (
    NotificationSetting,
    PushNotification,
    UserDevice,
)

logger = logging.getLogger("django.server")


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
            comment_noti_msg = PushNotificationTemplate(comment_author.nickname).comment_noti_tmpl(is_reply=True)
        else:  # 댓글인 경우
            noti_target_user = target_object.author
            comment_noti_msg = PushNotificationTemplate(comment_author.nickname).comment_noti_tmpl(
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

        message = PushNotificationTemplate(liked_user.nickname).like_noti_tmpl(object_str)
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

        message = PushNotificationTemplate(follower.nickname).follow_noti_tmpl()
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
        record_message = PushNotificationRecordTemplate(liked_user.nickname).like_noti_tmpl(object_str)

        self.save_push_notification(liked_obj_author, "like", data, record_message)

        logger.info(f"좋아요 알림 저장 완료 - liked_obj_id: {liked_obj.id}, liked_user: {liked_user.id}")

    def save_push_notification_follow(self, follower: CustomUser, followee: CustomUser):
        """
        팔로우 알림 저장
        """

        record_message = PushNotificationRecordTemplate(follower.nickname).follow_noti_tmpl()
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
