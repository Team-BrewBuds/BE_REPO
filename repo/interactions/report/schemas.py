from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from .serializers import ReportSerializer

Report_TAG = "Report"


class ReportSchema:
    report_post_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="object_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="신고할 대상의 타입",
                enum=["post", "tasted_record", "comment"],
            ),
            OpenApiParameter(name="object_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH, description="신고할 대상의 ID"),
        ],
        request=ReportSerializer,
        responses={
            201: ReportSerializer,
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
            404: OpenApiResponse(description="신고할 대상을 찾을 수 없음"),
            409: OpenApiResponse(description="이미 신고한 컨텐츠입니다"),
        },
        summary="컨텐츠 신고",
        description="""
            게시글, 시음기록, 댓글에 대한 신고를 생성합니다.

            **Path Parameters:**
            - object_type: "post" 또는 "tasted_record" 또는 "comment"
            - object_id: 신고할 대상의 ID

            **Request Body:**
            - reason: 신고 사유 (필수)

            담당자: hwstar1204
        """,
        tags=[Report_TAG],
    )

    report_schema_view = extend_schema_view(
        post=report_post_schema,
    )
