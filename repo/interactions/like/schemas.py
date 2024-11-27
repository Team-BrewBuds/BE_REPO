from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

Like_TAG = "Like"


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
        tags=[Like_TAG],
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
        tags=[Like_TAG],
    )

    like_schema_view = extend_schema_view(post=like_post_schema, delete=like_delete_schema)
