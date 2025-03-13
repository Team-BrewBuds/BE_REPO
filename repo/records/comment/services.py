from django.db.models import Prefetch, QuerySet

from repo.common.exception.exceptions import NotFoundException, ValidationException
from repo.interactions.relationship.services import RelationshipService
from repo.profiles.models import CustomUser
from repo.records.models import Comment, Post, TastedRecord


class CommentService:
    """
    댓글 관련 비즈니스 로직을 처리하는 서비스 클래스

    Attributes:
        object_type: 댓글 대상 객체 타입
        object_id: 댓글 대상 객체 ID
        target_model: 댓글 대상 모델 클래스
        target_object: 댓글 대상 객체 (Post, TastedRecord)
        relationship_service: 관계 서비스 인스턴스
    """

    model_map = {"post": Post, "tasted_record": TastedRecord}

    def __init__(self, object_type: str = None, object_id: int = None):
        self.relationship_service = RelationshipService()

        # 댓글 목록 조회나 생성 시
        if object_type and object_id:
            if object_type not in self.model_map:
                raise ValidationException(detail="Invalid object type", code="validation_error")

            self.object_type = object_type
            self.object_id = object_id
            self.target_model = self.model_map[object_type]
            self.target_object = self._get_target_object()

    def _get_target_object(self) -> Post | TastedRecord:
        """댓글이 달린 대상 객체(Post/TastedRecord) 조회"""
        try:
            return self.target_model.objects.get(id=self.object_id)
        except self.target_model.DoesNotExist as e:
            raise NotFoundException(detail="Target object not found", code="not_found") from e

    @classmethod
    def get_comment_by_id(cls, comment_id: int) -> Comment:
        """댓글 ID로 단일 댓글 조회"""
        try:
            return Comment.objects.filter(id=comment_id).select_related("author").first()
        except Comment.DoesNotExist as e:
            raise NotFoundException(detail="Comment not found", code="not_found") from e

    def get_comment_detail(self, comment: Comment) -> Comment:
        """댓글 상세 조회"""
        comment.replies_list = comment.replies.all()
        return comment

    def update_comment(self, comment: Comment, validated_data: dict) -> Comment:
        """댓글 수정"""
        comment.content = validated_data.get("content", comment.content)
        comment.save()
        return comment

    def delete_comment(self, comment: Comment) -> None:
        """댓글 삭제"""
        if comment.parent is None:
            comment.is_deleted = True
            comment.content = "삭제된 댓글입니다."
            comment.save()
        else:
            comment.delete()

    def get_comment_list(self, user: CustomUser) -> QuerySet[Comment]:
        """댓글 목록 조회"""
        target_object_comments = self.target_object.comment_set

        block_users = list(self.relationship_service.get_unique_blocked_user_list(user.id))
        user_liked_comments = set(target_object_comments.filter(like_cnt=user.id).values_list("id", flat=True))

        base_queryset = (
            self.target_object.comment_set.filter(parent=None)
            .exclude(author__in=block_users)
            .select_related("author")
            .prefetch_related(
                Prefetch(
                    "replies",
                    queryset=Comment.objects.select_related("author")
                    .exclude(author__in=block_users)
                    .order_by("id")
                    .prefetch_related(Prefetch("like_cnt", queryset=CustomUser.objects.filter(id=user.id))),
                ),
                Prefetch("like_cnt", queryset=CustomUser.objects.filter(id=user.id)),
            )
        )

        user_latest_comment = base_queryset.filter(author=user).order_by("-id").first()

        comments = list(base_queryset.exclude(id=user_latest_comment.id if user_latest_comment else None).order_by("id"))

        # 사용자의 최신 댓글 맨 앞에 추가
        if user_latest_comment:
            comments = [user_latest_comment] + comments

        for comment in comments:
            comment.replies_list = list(comment.replies.all())
            comment.is_user_liked = comment.id in user_liked_comments

            for reply in comment.replies_list:
                reply.is_user_liked = reply.id in user_liked_comments

        return comments

    def create_comment(self, user: CustomUser, validated_data: dict) -> Comment:
        """댓글 생성"""
        if self.target_object is None:
            raise NotFoundException(detail="Target object not found", code="not_found")

        comment_data = {
            "author": user,
            "content": validated_data.get("content"),
            "parent": validated_data.get("parent", None),
        }

        if isinstance(self.target_object, Post):
            comment_data["post"] = self.target_object
        elif isinstance(self.target_object, TastedRecord):
            comment_data["tasted_record"] = self.target_object

        return Comment.objects.create(**comment_data)
