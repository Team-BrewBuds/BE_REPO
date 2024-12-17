from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from .serializers import NoteResponseSerializer

Note_Tag = "Note"


class NoteSchema:
    note_post_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="object type",
                enum=["post", "tasted_record", "bean"],
            ),
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="object id",
            ),
        ],
        responses={
            201: NoteResponseSerializer,
            400: OpenApiResponse(description="잘못된 요청 (유효하지 않은 object_type 또는 object_id)"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="대상 객체를 찾을 수 없음"),
            409: OpenApiResponse(description="이미 노트가 존재함"),
        },
        summary="노트 생성",
        description="""
            사용자가 특정 컨텐츠(게시글, 시음기록, 원두)에 대해 노트를 생성

            **Path Parameters:**
            - object_type (string): "post" 또는 "tasted_record" 또는 "bean"
            - object_id (integer): 노트를 생성할 대상 객체의 ID

            **응답 코드:**
            - 201: 노트 생성 성공
            - 400: 잘못된 요청 (유효하지 않은 object_type 또는 object_id)
            - 401: 인증되지 않은 사용자
            - 404: 대상 객체를 찾을 수 없음
            - 409: 이미 해당 객체에 대한 노트가 존재함

            담당자: hwstar1204
        """,
        tags=[Note_Tag],
    )

    note_delete_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="object type",
                enum=["post", "tasted_record", "bean"],
            ),
            OpenApiParameter(
                name="object_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="object id",
            ),
        ],
        responses={
            204: OpenApiResponse(description="노트 삭제 성공"),
            400: OpenApiResponse(description="잘못된 요청 (유효하지 않은 object_type 또는 object_id)"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="노트를 찾을 수 없음"),
        },
        summary="노트 삭제",
        description="""
            사용자가 생성한 노트를 삭제

            **Path Parameters:**
            - object_type (string): "post" 또는 "tasted_record" 또는 "bean"
            - object_id (integer): 노트를 삭제할 대상 객체의 ID

            **응답 코드:**
            - 204: 노트 삭제 성공
            - 400: 잘못된 요청 (유효하지 않은 object_type 또는 object_id)
            - 401: 인증되지 않은 사용자
            - 404: 노트를 찾을 수 없음

            담당자: hwstar1204
        """,
        tags=[Note_Tag],
    )

    note_schema_view = extend_schema_view(post=note_post_schema, delete=note_delete_schema)
