from collections import defaultdict

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

    def get_comment_list(self, user: CustomUser) -> list[Comment]:
        """댓글 목록 조회 (유저 최신 댓글 우선 정렬)"""

        # 차단한 유저들 필터링
        blocked_users = set(self.relationship_service.get_unique_blocked_user_list(user.id))

        base_queryset = self.target_object.comment_set.select_related("author", "parent").exclude(author__in=blocked_users)

        # 유저가 좋아요한 댓글들 ID
        user_liked_comments_ids = set(base_queryset.filter(like_cnt=user.id).values_list("id", flat=True))

        # 유저가 작성한 최신 부모 댓글
        user_recent_comment: Comment | None = base_queryset.filter(author=user, parent=None).order_by("-id").first()

        root_comments: list[Comment] = []
        child_comments_dict: dict[int, list[Comment]] = defaultdict(list)
        comments = list(base_queryset.order_by("id").all())

        # 댓글 분류 및 좋아요 상태 설정
        for comment in comments:
            comment.is_user_liked = comment.id in user_liked_comments_ids

            if comment.parent_id:  # 대댓글
                child_comments_dict[comment.parent_id].append(comment)
            else:  # 부모 댓글
                root_comments.append(comment)

        # 최상위 댓글의 대댓글의 깊이를 제거하고 DFS 순서대로 정렬하여 최상위 댓글의 replies_list로 저장
        for parent in root_comments:
            parent.replies_list = self.get_replies_to_one_depths_by_dfs(parent, child_comments_dict)

        # 유저의 최신 부모 댓글 우선순위 적용
        if user_recent_comment:
            user_recent_comment = root_comments.pop(root_comments.index(user_recent_comment))
            root_comments.insert(0, user_recent_comment)

        return root_comments

    def get_comment_list_for_annonymouse(self) -> list[Comment]:
        """익명 유저 댓글 목록 조회"""
        comments = self.target_object.comment_set.select_related("author", "parent").order_by("id").all()

        root_comments: list[Comment] = []
        child_comments_dict: dict[int, list[Comment]] = defaultdict(list)

        for comment in comments:
            comment.is_user_liked = False

            if comment.parent_id:
                child_comments_dict[comment.parent_id].append(comment)
            else:
                root_comments.append(comment)

        for parent in root_comments:
            parent.replies_list = self.get_replies_to_one_depths_by_dfs(parent, child_comments_dict)

        return root_comments

    def get_replies_to_one_depths_by_dfs(self, parent: Comment, child_dict: dict[int, list[Comment]]) -> list[Comment]:
        """재귀참조하는 부모 댓글의 대댓글들의 깊이를 제거하고 DFS 순서대로 정렬 (부모 댓글 제외)"""
        result: list[Comment] = []
        stack = child_dict[parent.id][::-1]  # 부모 댓글의 대댓글들

        while stack:
            curr_comment = stack.pop()
            result.append(curr_comment)
            cur_commnet_child = child_dict[curr_comment.id][::-1]
            stack.extend(cur_commnet_child)

        return result
