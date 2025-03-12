from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.beans.serializers import (
    BeanDetailSerializer,
    BeanSerializer,
    UserBeanSerializer,
)
from repo.common.serializers import PageNumberSerializer
from repo.search.serializers import TastedRecordSearchSerializer

BeansTag = "beans"


class BeanSchema:
    bean_name_search_schema = extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(name="name", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="원두명"),
        ],
        responses={200: BeanSerializer(many=True)},
        summary="원두명 검색",
        description="""
               시음기록 작성시 원두 선택을 위해 사용
               - name 파라미터가 있으면 해당 원두명을 포함하는 원두 리스트를 가져온다.
               - name 파라미터가 없으면 모든 원두 리스트를 가져온다.
               - page_size = 20

               담당자 : hwstar1204
           """,
        tags=[BeansTag],
    )


class UserBeanListSchema:
    user_bean_list_get_schema = extend_schema(
        responses={
            200: UserBeanSerializer(many=True),
            404: OpenApiResponse(description="Not Found"),
        },
        parameters=[
            OpenApiParameter(name="bean_type", type=str, enum=["single", "blend"]),
            OpenApiParameter(
                name="origin_country",
                type=str,
                enum=[
                    "케냐",
                    "과테말라",
                    "에티오피아",
                    "브라질",
                    "콜비아",
                    "인도네시아",
                    "온두라스",
                    "탄자니아",
                    "르완다",
                ],
                required=False,
            ),
            OpenApiParameter(name="is_decaf", type=bool, enum=[True, False], required=False),
            OpenApiParameter(name="avg_star_min", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="avg_star_max", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="roast_point_min", type=int, enum=range(0, 6), required=False),
            OpenApiParameter(name="roast_point_max", type=int, enum=range(0, 6), required=False),
            OpenApiParameter(
                name="ordering",
                type=str,
                enum=["-note__created_at", "-avg_star", "-tasted_records_cnt"],
                required=False,
            ),
        ],
        summary="유저 찜한 원두 리스트 조회",
        description="""
            특정 사용자가 저장한 원두 리스트를 조회합니다.
            필터링: 원두 종류, 원산지, 디카페인 여부, 평균 별점, 로스팅
            정렬: 노트 생성일, 평균 별점, 시음기록 수
            담당자 : hwstar1204
        """,
        tags=[BeansTag],
    )

    user_bean_list_schema_view = extend_schema_view(get=user_bean_list_get_schema)


class BeanDetailSchema:
    bean_detail_get_schema = extend_schema(
        responses={
            200: BeanDetailSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="원두 세부 정보 조회",
        description="원두 세부 정보를 조회합니다. 담당자: blakej2432",
    )

    bean_detail_schema_view = extend_schema_view(get=bean_detail_get_schema)


class BeanTastedRecordSchema:
    bean_tasted_record_get_schema = extend_schema(
        responses={200: TastedRecordSearchSerializer},
        summary="특정 원두 관련 시음 기록 리스트 조회",
        description="특정 원두 관련 시음 기록을 조회합니다. 담당자: blakej2432",
    )

    bean_tasted_record_schema_view = extend_schema_view(get=bean_tasted_record_get_schema)
