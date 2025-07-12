from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer
from repo.records.tasted_record.serializers import (
    TastedRecordCreateUpdateSerializer,
    TastedRecordDetailSerializer,
    TastedRecordListSerializer,
    UserTastedRecordSerializer,
)

TastedRecord_Tag = "TastedRecord"


class TastedRecordSchema:
    tasted_record_list_get_schema = extend_schema(
        parameters=[PageNumberSerializer],
        responses={200: TastedRecordListSerializer},
        summary="홈 [시음기록] 피드 조회",
        description="""
            홈 피드의 시음기록들을 최신순으로 가져옵니다.
            - 순서: 팔로잉, 일반
            - 정렬: 최신순 (회원/비회원)
            - 페이지네이션 적용 (12개)
            - 30분이내 조회하지않은 시음기록 가져옵니다.
            - 프라이빗한 시음기록은 제외

            Notice:

            담당자: hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_create_post_schema = extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            201: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request (taste_review.star type: float)"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        summary="시음기록 생성",
        description="""
            단일 시음기록을 생성합니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_list_create_schema_view = extend_schema_view(get=tasted_record_list_get_schema, post=tasted_record_create_post_schema)

    tasted_record_detail_get_schema = extend_schema(
        responses={200: TastedRecordDetailSerializer},
        summary="시음기록 상세 조회",
        description="""
            시음기록의 상세 정보를 가져옵니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_put_schema = extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            200: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
        summary="시음기록 수정",
        description="""
            시음기록의 정보를 수정합니다. (전체 수정)
            원두 정보는 수정 불가능합니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_patch_schema = extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            200: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
        summary="시음기록 수정",
        description="""
            시음기록의 정보를 수정합니다. (일부 수정)
            원두 정보는 수정 불가능합니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_delete_schema = extend_schema(
        responses={204: OpenApiResponse(description="No Content")},
        summary="시음기록 삭제",
        description="""
            시음기록을 삭제합니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_schema_view = extend_schema_view(
        get=tasted_record_detail_get_schema,
        put=tasted_record_detail_put_schema,
        patch=tasted_record_detail_patch_schema,
        delete=tasted_record_detail_delete_schema,
    )


class UserTastedRecordListSchema:
    user_tasted_record_list_get_schema = extend_schema(
        parameters=[
            OpenApiParameter(name="bean_type", type=str, enum=["single", "blend"], required=False),
            OpenApiParameter(
                name="origin_country",
                type=str,
                enum=[
                    "케냐",
                    "과테말라",
                    "에티오피아",
                    "브라질",
                    "콜롬비아",
                    "인도네시아",
                    "온두라스",
                    "탄자니아",
                    "르완다",
                ],
                required=False,
            ),
            OpenApiParameter(name="star_min", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="star_max", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="is_decaf", type=bool, enum=[True, False], required=False),
            OpenApiParameter(name="roast_point_min", type=float, required=False),
            OpenApiParameter(name="roast_point_max", type=float, required=False),
            OpenApiParameter(name="ordering", type=str, enum=["-created_at", "-taste_review__star", "-likes"], required=False),
        ],
        responses={
            200: UserTastedRecordSerializer(many=True),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="유저 시음기록 리스트 조회",
        description="특정 사용자의 시음기록 리스트를 필터링하여 조회합니다.",
        tags=[TastedRecord_Tag],
    )

    user_tasted_record_list_schema_view = extend_schema_view(get=user_tasted_record_list_get_schema)
