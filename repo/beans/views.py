from collections import Counter

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.beans.schemas import *
from repo.beans.serializers import (
    BeanDetailSerializer,
    BeanSerializer,
    UserBeanSerializer,
)
from repo.beans.services import BeanService
from repo.common.filters import BeanFilter
from repo.interactions.note.models import Note
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


@BeanDetailSchema.bean_detail_schema_view
class BeanDetailView(APIView):
    """
    원두 세부 정보 API
    Args:
        request: 원두 ID(id)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 평균 별점(avg_star), 시음기록 개수(record_count), 원두 세부 정보와 가장 많이 나온 맛 4개의 리스트(top_flavors)를 포함한 원두 상세 데이터.
    담당자: blakej2432
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        bean = get_object_or_404(Bean.objects.select_related("bean_taste"), id=id, is_official=True)
        related_records = bean.tastedrecord_set.select_related("taste_review")

        aggregate_data = related_records.aggregate(avg_star=Avg("taste_review__star"), record_count=Count("id"))
        flavors = related_records.values_list("taste_review__flavor", flat=True)

        avg_star = round(aggregate_data["avg_star"] or 0, 1)
        record_count = aggregate_data["record_count"] or 0
        top_flavors = self.get_flavor_percentages(flavors) if record_count > 0 else []
        is_user_noted = Note.objects.filter(bean=bean, author=request.user).exists()

        bean.avg_star = avg_star
        bean.record_count = record_count
        bean.top_flavors = top_flavors
        bean.is_user_noted = is_user_noted

        return Response(BeanDetailSerializer(bean).data, status=status.HTTP_200_OK)

    def get_flavor_percentages(self, flavors: list[str]) -> list[dict[str, str | int]]:
        split_flavors = []
        for flavor_str in flavors:
            if flavor_str:
                split_flavors.extend(flavor_str.split(","))  # 쉼표 기준 맛 분리

        flavor_counter = Counter(split_flavors)
        total_flavor_count = sum(flavor_counter.values())

        flavor_counter = Counter(split_flavors)
        total_flavor_count = flavor_counter.total()
        flavor_items = flavor_counter.items()

        top_flavors = []
        for flavor, count in flavor_items:
            top_flavors.append({"flavor": flavor, "percentage": int(round((count / total_flavor_count) * 100, 0))})

        top_flavors.sort(key=lambda x: x["percentage"], reverse=True)

        return top_flavors


@BeanTastedRecordSchema.bean_tasted_record_schema_view
class BeanTastedRecordView(APIView):
    """
    특정 원두 관련 시음 기록 리스트 API
    Args:
        request: 원두 ID(id)를 포함한 클라이언트 요청. 페이지 번호(page)를 쿼리 파라미터로 전달하여 페이징 처리.
    Returns:
        JSON 응답: 요청된 원두의 시음 기록 리스트. 페이징 정보와 함께 반환.
    담당자: blakej2432
    """

    def get(self, request, id):
        bean = get_object_or_404(Bean, id=id, is_official=True)
        records = TastedRecord.objects.filter(bean=bean).select_related("author", "bean", "taste_review")

        paginator = PageNumberPagination()
        paginator.page_size = 4
        paginated_records = paginator.paginate_queryset(records, request)

        serializer = TastedRecordSearchSerializer(paginated_records, many=True)

        return paginator.get_paginated_response(serializer.data)
