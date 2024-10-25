from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer
from repo.records.posts.serializers import PostListSerializer
from repo.records.serializers import CommentSerializer, LikeSerializer, NoteSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer

Feed_Tag = "Feed"
Like_Tage = "Like"
Note_Tag = "Note"
Comment_Tag = "Comment"
Image_Tag = "Image"


class FeedSchema:
    feed_get_schema = extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="feed_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="feed type",
                enum=["following", "common", "refresh"],
            ),
        ],
        responses={200: [TastedRecordListSerializer, PostListSerializer]},
        summary="홈 [전체] 피드",
        description="""
            following:
            홈 [전체] 사용자가 팔로잉한 유저들의 1시간 이내 작성한 시음기록과 게시글을 랜덤순으로 가져오는 함수
            30분이내 조회한 기록, 프라이빗한 시음기록은 제외

            common:
            홈 [전체] 일반 시음기록과 게시글을 최신순으로 가져오는 함수
            30분이내 조회한 기록, 프라이빗한 시음기록은 제외

            refresh:
            홈 [전체] 시음기록과 게시글을 랜덤순으로 반환하는 API
            프라이빗한 시음기록은 제외

            response:
            TastedRecordListSerializer or PostListSerializer
            (아래 Schemas 참조)

            담당자 : hwstar1204
        """,
        tags=[Feed_Tag],
    )

    feed_schema_view = extend_schema_view(get=feed_get_schema)


class LikeSchema:
    like_post_schema = extend_schema(
        request=LikeSerializer,
        responses={
            201: OpenApiResponse(description="like success"),
            200: OpenApiResponse(description="like cancel"),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="좋아요 추가/취소 API",
        description="""
            object_type : "post" or "tasted_record" or "comment"
            object_id : 좋아요를 처리할 객체의 ID

            response:
                201: 좋아요 추가, 200: 좋아요 취소

            담당자 : hwstar1204
        """,
        tags=[Like_Tage],
    )

    like_schema_view = extend_schema_view(post=like_post_schema)


class NoteSchema:
    note_post_schema = extend_schema(
        request=NoteSerializer,
        responses={
            200: OpenApiResponse(description="Note already exists"),
            201: OpenApiResponse(description="Note created"),
        },
        summary="노트 생성",
        description="""
            object_type : "post" 또는 "tasted_record"
            object_id : 노트를 처리할 객체의 ID

            담당자: hwstar1204
        """,
        tags=[Note_Tag],
    )

    note_schema_view = extend_schema_view(post=note_post_schema)


class NoteDetailSchema:
    note_detail_delete_schema = extend_schema(
        responses={
            200: OpenApiResponse(description="Note deleted"),
            404: OpenApiResponse(description="Note not found"),
        },
        summary="노트 삭제",
        description="""
                object_type : "post" 또는 "tasted_record"
                object_id : 노트를 처리할 객체의 ID

                담당자: hwstar1204
            """,
        tags=[Note_Tag],
    )

    note_detail_schema_view = extend_schema_view(delete=note_detail_delete_schema)


class CommentSchema:
    comment_get_schema = extend_schema(
        parameters=[PageNumberSerializer],
        responses={200: CommentSerializer},
        summary="댓글 리스트 조회",
        description="""
            - object_type : "post" 또는 "tasted_record"
            - object_id : 댓글을 처리할 객체의 ID
            - content : 댓글 내용
            담당자: hwstar1204
        """,
        tags=[Comment_Tag],
    )

    comment_post_schema = extend_schema(
        request=CommentSerializer,
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
        tags=[Comment_Tag],
    )

    comment_schema_view = extend_schema_view(get=comment_get_schema, post=comment_post_schema)


class CommentDetailSchema:
    comment_detail_get_schema = extend_schema(
        responses={200: CommentSerializer},
        summary="댓글 상세 조회",
        description="""
            id : 댓글 ID
        """,
        tags=[Comment_Tag],
    )

    comment_detail_put_schema = extend_schema(
        request=CommentSerializer,
        responses={
            200: OpenApiResponse(description="Comment updated"),
            404: OpenApiResponse(description="Comment not found"),
        },
        summary="댓글 수정",
        description="""
            id : 댓글 ID
            content : 수정할 댓글 내용
        """,
        tags=[Comment_Tag],
    )

    comment_detail_patch_schema = extend_schema(
        request=CommentSerializer,
        responses={
            200: OpenApiResponse(description="Comment updated"),
            404: OpenApiResponse(description="Comment not found"),
        },
        summary="댓글 수정",
        description="""
            id : 댓글 ID
            content : 수정할 댓글 내용
        """,
        tags=[Comment_Tag],
    )

    comment_detail_delete_schema = extend_schema(
        responses={
            200: OpenApiResponse(description="Comment deleted"),
            404: OpenApiResponse(description="Comment not found"),
        },
        summary="댓글 삭제",
        description="""
            id : 댓글 ID
            soft delete : 부모 댓글이 없는 경우 소프트 삭제
        """,
        tags=[Comment_Tag],
    )

    comment_detail_schema_view = extend_schema_view(
        get=comment_detail_get_schema, put=comment_detail_put_schema, patch=comment_detail_patch_schema, delete=comment_detail_delete_schema
    )


class ImageSchema:
    image_post_schema = extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "photo_url": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "format": "binary",
                        },
                        "description": "이미지 파일 리스트",
                    }
                },
                "required": ["photo_url"],
            }
        },
        responses={
            201: OpenApiResponse(
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "example": 123},
                            "photo_url": {"type": "string", "example": "https://s3.amazonaws.com/bucket_name/uploads" "/photo1.jpg"},
                        },
                    },
                },
                description="이미지 업로드 성공",
            ),
            400: OpenApiResponse(description="잘못된 데이터 형식 또는 유효성 검증 실패"),
        },
        summary="이미지 업로드 API",
        description="여러 개의 이미지를 업로드하는 API. 업로드된 이미지는 고유 ID와 S3 URL로 반환됩니다.",
        tags=[Image_Tag],
    )

    image_delete_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="photo_id",
                description="삭제할 사진의 ID 목록 (쿼리 파라미터로 여러 개의 photo_id 전달)",
                required=True,
                type={"type": "array", "items": {"type": "integer"}},
            )
        ],
        responses={
            204: OpenApiResponse(description="성공적으로 삭제됨"),
            400: OpenApiResponse(description="잘못된 요청 (photo_id 누락 또는 잘못된 형식)"),
            404: OpenApiResponse(description="해당 ID의 사진을 찾을 수 없음"),
            500: OpenApiResponse(description="서버 에러"),
        },
        summary="이미지 삭제 API",
        description="여러 개의 이미지를 삭제하는 API. 삭제할 이미지의 ID를 쿼리 파라미터로 전달하면 해당 이미지가 삭제됩니다.",
        tags=[Image_Tag],
    )

    image_schema_view = extend_schema_view(post=image_post_schema, delete=image_delete_schema)
