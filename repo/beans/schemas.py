from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from repo.beans.serializers import BeanSerializer
from repo.common.serializers import PageNumberSerializer

BeansTag = "beans"


class BeanSchema:
    bena_name_list_schema = extend_schema(
        parameters=[PageNumberSerializer],
        responses=BeanSerializer(many=True),
        summary="모든 원두 리스트 조회",
        description="""
            모든 원두 리스트 가져오는 API
            - page_size = 20

            담당자 : hwstar1204
        """,
        tags=[BeansTag],
    )

    bean_name_search_schema = extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(name="name", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="원두명"),
        ],
        responses=BeanSerializer(many=True),
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
