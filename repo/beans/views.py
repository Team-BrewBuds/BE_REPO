from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
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
from repo.records.models import TastedRecord


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
    원두 상세 정보 API
    담당자: blakej2432
    """

    def get(self, request, id):
        bean = get_object_or_404(Bean, id=id)

        stats = TastedRecord.objects.filter(bean=bean).aggregate(avg_star=Avg("taste_review__star"), record_count=Count("id"))

        serializer = BeanDetailSerializer(bean, context={"avg_star": stats["avg_star"] or 0, "record_count": stats["record_count"] or 0})

        return Response(serializer.data, status=status.HTTP_200_OK)
