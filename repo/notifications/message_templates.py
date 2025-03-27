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
            "title": "{sender_name}",
            "body": "{content}"
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

    def comment_noti_template(self, body: str) -> dict:
        """댓글 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["author"]
        return {
            "title": template["title"].format(sender_name=self.sender_name),
            "body": template["body"].format(content=body),
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
        "author": {
            "title": "{object_type}",
            "body": "{sender_name}님이 버디님의 {object_type}에 댓글을 남겼어요. \n {content}"
        },
        "comment_author": {
            "title": "{object_type}",
            "body": "'{object_title}' {object_type}에 {sender_name}님이 댓글을 남겼어요. \n {content}"
        },
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

    def comment_noti_template_author(self, object_type: str, content: str) -> Dict[str, str]:
        """나의 게시물에 댓글 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["author"]
        return {
            "title": template["title"].format(object_type=object_type),
            "body": template["body"].format(sender_name=self.sender_name, object_type=object_type, content=content),
        }

    def comment_noti_template_comment_author(self, object_type: str, object_title: str, content: str) -> Dict[str, str]:
        """내가 댓글 단 게시물의 작성자에게 알림 메시지 템플릿"""
        template = self.MESSAGE_FORMATS["comment_author"]
        return {
            "title": template["title"].format(object_type=object_type),
            "body": template["body"].format(
                sender_name=self.sender_name, object_type=object_type, object_title=object_title, content=content
            ),
        }

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
