from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer
from repo.records.posts.serializers import PostListSerializer
from repo.records.serializers import CommentSerializer, ReportSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer

Feed_Tag = "Feed"
Like_Tage = "Like"
Note_Tag = "Note"
Comment_Tag = "Comment"
Photo_Tag = "Photo"
Report_TAG = "Report"


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

            Notice:
            - like_cnt에서 likes로 변경
            - comments(댓글 수), is_user_noted(사용자 저장여부) 추가 됨
            - 비회원일경우 랜덤으로 시음기록을 가져옵니다. (feed_type 쿼리 파라미터 미사용)
            - 차단하거나 나를 차단한 사용자의 글은 제외됩니다.
            - **common에서 시음기록 다음 게시글이 나오는 버그가 해결되어 두 리스트가 섞여서 최신순으로 나옵니다.**

            담당자 : hwstar1204
        """,
        tags=[Feed_Tag],
    )

    feed_schema_view = extend_schema_view(get=feed_get_schema)


class LikeSchema:
    like_post_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="object type",
                enum=["post", "tasted_record", "comment"],
            ),
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="object id",
            ),
        ],
        responses={
            201: OpenApiResponse(description="like success"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
            409: OpenApiResponse(description="Already liked"),
        },
        summary="좋아요 추가",
        description="""
            object_type : "post" or "tasted_record" or "comment"
            object_id : 좋아요를 처리할 객체의 ID

            담당자 : hwstar1204
        """,
        tags=[Like_Tage],
    )

    like_delete_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="object type",
                enum=["post", "tasted_record", "comment"],
            ),
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="object id",
            ),
        ],
        responses={
            204: OpenApiResponse(description="like deleted"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="좋아요 삭제",
        description="""
                object_type : "post" or "tasted_record" or "comment"
                object_id : 좋아요를 처리할 객체의 ID

                담당자 : hwstar1204
            """,
        tags=[Like_Tage],
    )

    like_schema_view = extend_schema_view(post=like_post_schema, delete=like_delete_schema)


class NoteSchema:
    note_post_schema = extend_schema(
        responses={
            200: OpenApiResponse(description="Note already exists"),
            201: OpenApiResponse(description="Note created"),
        },
        summary="노트 생성",
        description="""
            object_type : "post" 또는 "tasted_record" 또는 "bean"
            object_id : 노트를 처리할 객체의 ID

            담당자: hwstar1204
        """,
        tags=[Note_Tag],
    )

    note_delete_schema = extend_schema(
        responses={
            200: OpenApiResponse(description="Note deleted"),
            404: OpenApiResponse(description="Note not found"),
        },
        summary="노트 삭제",
        description="""
            object_type : "post" 또는 "tasted_record" 또는 "bean"
            object_id : 노트를 처리할 객체의 ID

            담당자: hwstar1204
        """,
        tags=[Note_Tag],
    )

    note_schema_view = extend_schema_view(post=note_post_schema, delete=note_delete_schema)


class CommentSchema:
    comment_get_schema = extend_schema(
        parameters=[PageNumberSerializer],
        responses={200: CommentSerializer},
        summary="댓글 리스트 조회",
        description="""
            - object_type : "post" 또는 "tasted_record"
            - object_id : 댓글을 처리할 객체의 ID
            - content : 댓글 내용
            notice : 차단한 사용자의 댓글은 제외됩니다.
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


class PhotoSchema:
    photo_post_schema = extend_schema(
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
                            "is_representative": {"type": "boolean", "example": True},
                        },
                    },
                },
                description="이미지 업로드 성공",
            ),
            400: OpenApiResponse(description="잘못된 데이터 형식 또는 유효성 검증 실패"),
        },
        summary="이미지 업로드 API",
        description="""
            여러 개의 이미지를 업로드하는 API. 업로드된 이미지는 고유 ID와 S3 URL로 반환됩니다.
            notice:
            - 대표 사진은 요청 데이터의 첫 번째 이미지로 설정됩니다.
            - 대표 사진의 파일명은 main_로 변경됩니다.
            대표 사진 여부 판단요소:
            - 사진명이 main_ 으로 시작합니다.
            - 해당 사진 헤더의 메타데이터에 x-amz-meta-is-representative = true 입니다.
        """,
        tags=[Photo_Tag],
    )

    photo_put_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="사진을 수정할 객체의 ID (PK)",
            ),
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="사진을 수정할 객체의 타입",
                enum=["post", "tasted_record"],
            ),
        ],
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
                        "description": "새로운 이미지 파일 리스트",
                    }
                },
                "required": ["photo_url"],
            }
        },
        responses={
            200: OpenApiResponse(
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "example": 123},
                            "photo_url": {"type": "string", "example": "https://s3.amazonaws.com/bucket_name/uploads/photo1.jpg"},
                            "is_representative": {"type": "boolean", "example": True},
                        },
                    },
                },
                description="이미지 수정 성공",
            ),
            400: OpenApiResponse(description="잘못된 데이터 형식"),
            403: OpenApiResponse(description="권한 없음"),
            404: OpenApiResponse(description="객체를 찾을 수 없음"),
            500: OpenApiResponse(description="서버 에러"),
        },
        summary="이미지 수정 API",
        description="""
            게시글이나 시음기록에 등록된 사진을 수정하는 API입니다.
            - 기존 사진은 모두 삭제되고 새로운 사진으로 대체됩니다.
            - 첫 번째 사진이 대표 사진으로 설정됩니다.
            - 작성자만 수정할 수 있습니다.
        """,
        tags=[Photo_Tag],
    )

    photo_delete_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="사진 삭제할 객체의 ID(PK)",
            ),
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="사진 삭제할 객체의 타입",
                enum=["post", "tasted_record"],
            ),
        ],
        responses={
            204: OpenApiResponse(description="성공적으로 삭제됨"),
            400: OpenApiResponse(description="잘못된 요청 (object_id, object_type 누락 또는 잘못된 형식)"),
            404: OpenApiResponse(description="해당 객체의 사진을 찾을 수 없음"),
            500: OpenApiResponse(description="서버 에러"),
        },
        summary="이미지 삭제 API",
        description="""
            삭제할 객체의 이미지들을 삭제하는 API.
            삭제할 객체 타입과 해당 객체의 ID를 쿼리 파라미터로 전달하면 해당 이미지들이 삭제됩니다.
        """,
        tags=[Photo_Tag],
    )

    photo_schema_view = extend_schema_view(post=photo_post_schema, put=photo_put_schema, delete=photo_delete_schema)


class ProfilePhotoSchema:
    profile_photo_post_schema = extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "photo_url": {
                        "type": "string",
                        "format": "binary",
                        "description": "프로필 이미지 파일",
                    }
                },
                "required": ["photo_url"],
            }
        },
        responses={
            201: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "photo_url": {"type": "string", "example": "https://s3.amazonaws.com/bucket_name/profiles/main_uuid.jpg"}
                    },
                },
                description="프로필 이미지 업로드 성공",
            ),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            500: OpenApiResponse(description="서버 에러"),
        },
        summary="프로필 이미지 업로드 API",
        description="""
            사용자의 프로필 이미지를 업로드하는 API
            notice:
            - 기존 프로필 이미지가 있다면 삭제됩니다. (수정시 기존 사진 삭제 후 업로드)
        """,
        tags=[Photo_Tag],
    )

    profile_photo_delete_schema = extend_schema(
        responses={
            204: OpenApiResponse(description="프로필 이미지 삭제 성공"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            500: OpenApiResponse(description="서버 에러"),
        },
        summary="프로필 이미지 삭제 API",
        description="사용자의 프로필 이미지를 삭제하는 API",
        tags=[Photo_Tag],
    )

    profile_photo_schema_view = extend_schema_view(post=profile_photo_post_schema, delete=profile_photo_delete_schema)


class ReportSchema:
    report_post_schema = extend_schema(
        request=ReportSerializer,
        responses={
            200: OpenApiResponse(description="duplicate report"),
            201: ReportSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="신고하기",
        description="""
            object_type : "post" 또는 "tasted_record" 또는 "comment"
            object_id : 신고할 객체의 ID
            reason : 신고 사유
        """,
        tags=[Report_TAG],
    )

    report_schema_view = extend_schema_view(post=report_post_schema)
