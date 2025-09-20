from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer

from .serializers import CommentInputSerializer, CommentOutputSerializer

Comment_TAG = "Comment"


class CommentSchema:
    comment_get_schema = extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="object type",
                enum=["post", "tasted_record"],
            ),
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="object id",
            ),
        ],
        responses={200: CommentOutputSerializer},
        summary="댓글 리스트 조회",
        description="""
            - object_type : "post" 또는 "tasted_record"
            - object_id : 댓글을 처리할 객체의 ID
            - content : 댓글 내용

            notice:
            - 차단한 사용자의 댓글은 제외됩니다. (대댓글 포함)
            - url 주소 끝에 '/'가 빠져있었어서 추가하였습니다.
            (해당 api를 사용하고있었다면 수정해주세요!!)
            담당자: hwstar1204
        """,
        tags=[Comment_TAG],
    )

    comment_post_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="object type",
                enum=["post", "tasted_record"],
            ),
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="object id",
            ),
        ],
        request=CommentInputSerializer,
        responses={
            200: OpenApiResponse(description="Comment created"),
            400: OpenApiResponse(description="Invalid data"),
        },
        summary="댓글 생성 (대댓글 포함)",
        description="""
            - object_type : "post" 또는 "tasted_record"
            - object_id : 댓글을 처리할 객체의 ID
            - content : 댓글 내용
            - parent_id : 대댓글인 경우 부모 댓글의 ID (optional)
            담당자: hwstar1204
        """,
        tags=[Comment_TAG],
    )

    comment_schema_view = extend_schema_view(get=comment_get_schema, post=comment_post_schema)


class CommentDetailSchema:
    comment_detail_get_schema = extend_schema(
        responses={200: CommentOutputSerializer},
        summary="댓글 상세 조회",
        description="""
            id : 댓글 ID
            replies : 해당 댓글의 대댓글 리스트를 포함하여 반환합니다.
            notice : 차단한 사용자의 댓글은 제외됩니다.
            담당자: hwstar1204
        """,
        tags=[Comment_TAG],
    )

    comment_detail_patch_schema = extend_schema(
        request=CommentInputSerializer,
        responses={
            200: OpenApiResponse(description="Comment updated"),
            404: OpenApiResponse(description="Comment not found"),
        },
        summary="댓글 수정",
        description="""
            id : 댓글 ID
            content : 수정할 댓글 내용
            담당자: hwstar1204
        """,
        tags=[Comment_TAG],
    )

    comment_detail_delete_schema = extend_schema(
        responses={
            204: OpenApiResponse(description="Comment deleted"),
            404: OpenApiResponse(description="Comment not found"),
        },
        summary="댓글 삭제",
        description="""
            id : 댓글 ID
            soft delete : 부모 댓글이 없는 경우 소프트 삭제
            담당자: hwstar1204
        """,
        tags=[Comment_TAG],
    )

    comment_detail_schema_view = extend_schema_view(
        get=comment_detail_get_schema, patch=comment_detail_patch_schema, delete=comment_detail_delete_schema
    )
