from typing import Dict

APP_NAME = "브루버즈"


class PushNotificationTemplate:
    """
    푸시 알림 메시지 템플릿
    - 알림 전송 시 사용
    """

    # fmt: off
    MESSAGE_FORMATS = {
        "author": {
            "title": APP_NAME,
            "body": "{content}"
        },
        "comment": {  # (댓글 작성시) 게시물 작성자에게 알림
            "title": APP_NAME,
            "body": "{sender_name}님이 버디님의 {object_type}에 댓글을 남겼어요."
        },
        "comment_reply": {  # (대댓글 작성시) 댓글 작성자에게 알림
            "title": APP_NAME,
            "body": "{sender_name}님이 버디님의 댓글에 답글을 남겼어요."
        },
        "like": {
            "title": APP_NAME,
            "body": "{sender_name}님이 버디님의 {object_type}을 좋아해요."
        },
        "follow": {
            "title": APP_NAME,
            "body": "{sender_name}님이 버디님을 팔로우하기 시작했어요."
        }
    }
    # fmt: on

    def __init__(self, sender_name: str):
        self.sender_name = sender_name

    def comment_noti_template(self, is_reply: bool = False, object_type: str = None) -> dict:
        """댓글 알림 메시지 템플릿"""
        if is_reply:
            template = self.MESSAGE_FORMATS["comment_reply"]
            return {
                "title": template["title"],
                "body": template["body"].format(sender_name=self.sender_name),
            }
        else:
            template = self.MESSAGE_FORMATS["comment"]
            return {
                "title": template["title"],
                "body": template["body"].format(sender_name=self.sender_name, object_type=object_type),
            }

    def like_noti_template(self, object_type: str = "게시물") -> dict:
        """좋아요 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["like"]
        return {
            "title": template["title"],
            "body": template["body"].format(sender_name=self.sender_name, object_type=object_type),
        }

    def follow_noti_template(self) -> dict:
        """팔로우 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["follow"]
        return {
            "title": template["title"],
            "body": template["body"].format(sender_name=self.sender_name),
        }


class PushNotificationRecordTemplate:
    """
    푸시 알림 메시지 저장 템플릿
    - 알림 기록 저장 후 조회시 사용
    """

    # fmt: off
    MESSAGE_FORMATS = {
        "like": {
            "title": "{object_type}",
            "body": "{sender_name}님이 버디님의 {object_type}을 좋아해요."
        },
        "follow": {
            "title": "신규 버디",
            "body": "{sender_name}님이 버디님을 팔로우하기 시작했어요."
        }
    }
    # fmt: on

    def __init__(self, sender_name: str):
        self.sender_name = sender_name

    def like_noti_template(self, object_type: str = "게시물") -> Dict[str, str]:
        """좋아요 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["like"]
        return {
            "title": template["title"].format(object_type=object_type),
            "body": template["body"].format(sender_name=self.sender_name, object_type=object_type),
        }

    def follow_noti_template(self) -> Dict[str, str]:
        """팔로우 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["follow"]
        return {"title": template["title"], "body": template["body"].format(sender_name=self.sender_name)}
