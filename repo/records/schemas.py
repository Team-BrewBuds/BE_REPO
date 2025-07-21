from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer, PhotoDetailSerializer
from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer

Feed_Tag = "Feed"
Photo_Tag = "Photo"


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
            홈 [전체] 사용자가 팔로잉한 유저들의 시음기록과 게시글을 최신순으로 가져오는 함수
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
            - 비회원일경우 feed_type 쿼리 파라미터 미사용
            - 차단하거나 나를 차단한 사용자의 글은 제외됩니다.

            담당자 : hwstar1204
        """,
        tags=[Feed_Tag],
    )
    feed_schema_view = extend_schema_view(get=feed_get_schema)


class FeedSchemaV2:
    feed_get_schema_v2 = extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="feed_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="feed type",
                enum=["refresh"],
            ),
        ],
        responses={200: [TastedRecordListSerializer, PostListSerializer]},
        summary="홈 [전체] 피드 (v2)",
        description="""
            게시글+시음기록 전체 피드 조회
            feed_type = None OR refresh

            None:
            - 비회원이라면 비회원용 피드 조회
            - 회원이라면 (following + common) 두개 api 대체 및 새로운 피드 조회 로직 적용

            refresh:
            - 홈 [전체] 시음기록과 게시글을 랜덤순으로 반환하는 API

            response:
            TastedRecordListSerializer or PostListSerializer
            (아래 Schemas 참조)
        """,
        tags=[Feed_Tag],
    )
    feed_schema_view_v2 = extend_schema_view(get=feed_get_schema_v2)


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
            201: PhotoDetailSerializer,
            400: OpenApiResponse(description="잘못된 데이터 형식 또는 유효성 검증 실패"),
            403: OpenApiResponse(description="권한 없음"),
            500: OpenApiResponse(description="서버 에러"),
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
            200: PhotoDetailSerializer,
            400: OpenApiResponse(description="잘못된 데이터 형식 또는 유효성 검증 실패"),
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
            400: OpenApiResponse(description="잘못된 데이터 형식 또는 유효성 검증 실패"),
            403: OpenApiResponse(description="권한 없음"),
            404: OpenApiResponse(description="해당 객체의 사진을 찾을 수 없음"),
            500: OpenApiResponse(description="서버 에러"),
        },
        summary="이미지 삭제 API",
        description="""
            삭제할 객체의 이미지들을 삭제하는 API.
            - 삭제할 객체 타입과 해당 객체의 ID를 쿼리 파라미터로 전달하면 해당 이미지들이 삭제됩니다.
            - 작성자만 삭제할 수 있습니다.
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
