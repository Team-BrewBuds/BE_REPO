from collections import Counter
from itertools import chain

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.beans.models import OfficialBean
from repo.beans.schemas import *
from repo.beans.serializers import (
    BeanDetailSerializer,
    BeanSerializer,
    UserBeanSerializer,
)
from repo.beans.services import BeanService
from repo.common.filters import BeanFilter
from repo.records.models import TastedRecord
from repo.search.serializers import TastedRecordSearchSerializer


@BeanSchema.bean_name_search_schema
class BeanNameSearchView(APIView):

    def __init__(self):
        self.bean_service = BeanService()

    def get(self, request):
        name = request.query_params.get("name")
        beans = self.bean_service.search_by_name(name).order_by("name")

        paginator = PageNumberPagination()
        paginator.page_size = 20
        paginated_beans = paginator.paginate_queryset(beans, request)

        serializer = BeanSerializer(paginated_beans, many=True)
        return paginator.get_paginated_response(serializer.data)


@UserBeanListSchema.user_bean_list_schema_view
class UserBeanListAPIView(generics.ListAPIView):
    serializer_class = UserBeanSerializer
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = BeanFilter
    ordering_fields = ["-note__created_at", "-avg_star", "-tasted_records_cnt"]

    def get_queryset(self):
        user_id = self.kwargs.get("id")
        ordering = self.request.query_params.get("ordering", "-note__created_at")
        queryset = BeanService().get_user_saved(user_id)
        return queryset.order_by(ordering)


class BeanDetailView(APIView):
    """
    원두 세부 정보 API
    Args:
        request: 원두 ID(id)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 평균 별점(avg_star), 시음기록 개수(record_count), 원두 세부 정보와 가장 많이 나온 맛 4개의 리스트(top_flavors)를 포함한 원두 상세 데이터.
    담당자: blakej2432
    """

    def get(self, request, id):
        official_bean = get_object_or_404(OfficialBean.objects.select_related("bean_taste"), id=id)

        stats = TastedRecord.objects.filter(bean__name=official_bean.name).aggregate(
            avg_star=Avg("taste_review__star"), record_count=Count("id")
        )

        flavors = TastedRecord.objects.filter(bean__name=official_bean.name).values_list("taste_review__flavor", flat=True)

        split_flavors = chain.from_iterable(flavor.split(", ") for flavor in flavors if flavor)
        flavor_counter = Counter(split_flavors)

        total_records = stats["record_count"] or 1
        top_flavors = [{"flavor": flavor, "percentage": (count * 100 // total_records)} for flavor, count in flavor_counter.most_common(4)]

        serializer = BeanDetailSerializer(
            official_bean,
            context={
                "avg_star": stats["avg_star"] or 0,
                "record_count": stats["record_count"] or 0,
                "top_flavors": top_flavors,
            },
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class BeanTastedRecordView(APIView):
    """
    시음 기록 리스트 API
    Args:
        request: 원두 ID(id)를 포함한 클라이언트 요청. 페이지 번호(page)를 쿼리 파라미터로 전달하여 페이징 처리.
    Returns:
        JSON 응답: 요청된 원두의 시음 기록 리스트. 페이징 정보와 함께 반환.
    담당자: blakej2432
    """

    def get(self, request, id):
        official_bean = get_object_or_404(OfficialBean, id=id)
        records = TastedRecord.objects.filter(bean__name=official_bean.name).select_related("author", "bean", "taste_review")

        paginator = PageNumberPagination()
        paginator.page_size = 4
        paginated_records = paginator.paginate_queryset(records, request)

        serializer = TastedRecordSearchSerializer(paginated_records, many=True)

        return paginator.get_paginated_response(serializer.data)
