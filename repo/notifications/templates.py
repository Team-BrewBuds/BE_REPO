class NotificationTemplate:
    """
    알림 메시지 템플릿
    """

    APP_NAME = "브루버즈"

    def __init__(self, user_name: str):
        self.title = self.APP_NAME
        self.user_name = user_name

    def comment_noti_template(self, body: str) -> dict:
        """댓글 알림 메시지 템플릿"""
        return {"title": self.title, "body": f"{self.user_name}님이 회원님의 게시물에 댓글을 남겼어요.\n{body}"}

    def like_noti_template(self, object_type: str = "게시물") -> dict:
        """좋아요 알림 메시지 템플릿"""
        return {"title": self.title, "body": f"{self.user_name}님이 회원님의 {object_type}을 좋아해요."}

    def follow_noti_template(self) -> dict:
        """팔로우 알림 메시지 템플릿"""
        return {"title": self.title, "body": f"{self.user_name}님이 회원님을 팔로우하기 시작했어요."}
