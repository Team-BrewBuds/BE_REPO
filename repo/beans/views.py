from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.beans.serializers import BeanSerializer
from repo.common.serializers import PageNumberSerializer


@extend_schema(
    parameters=[PageNumberSerializer],
    responses=BeanSerializer(many=True),
    summary="모든 원두 리스트 조회",
    description="""
        모든 원두 리스트 가져오는 API
        - page_size = 20

        담당자 : hwstar1204
    """,
    tags=["beans"],
)
class BeanNameListView(APIView):
    def get(self, request):
        beans = Bean.objects.all()

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)


@extend_schema(
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
    tags=["beans"],
)
class BeanNameSearchView(APIView):
    def get(self, request):
        name = request.query_params.get("name")
        if not name:
            return BeanNameListView().get(request)

        beans = Bean.objects.filter(name__contains=name).order_by("name")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)
