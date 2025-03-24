from django.db.models import (
    Avg,
    Count,
    ExpressionWrapper,
    FloatField,
    OuterRef,
    Q,
    Subquery,
)
from django.db.models.functions import Round
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.common.utils import get_paginated_response_with_class
from repo.profiles.models import CustomUser
from repo.records.models import Photo, Post, TastedRecord
from repo.search.filters import *
from repo.search.schemas import SearchSchema
from repo.search.serializers import *


@SearchSchema.buddy_search_schema_view
class BuddySearchView(APIView):
    """
    사용자 검색 API
    Args:
        request: 검색어(query)와 정렬 기준(sort_by)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 일치하는 사용자의 리스트, 정렬 기준 적용 가능.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = BuddySearchInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        users = CustomUser.objects.annotate(
            record_cnt=Count("tastedrecord"), follower_cnt=Count("relationships_to", filter=Q(relationships_to__relationship_type="follow"))
        )

        filterset = BuddyFilter(serializer.validated_data, queryset=users)
        filtered_users = filterset.qs

        return get_paginated_response_with_class(request, filtered_users, BuddySearchSerializer)


@SearchSchema.bean_search_schema_view
class BeanSearchView(APIView):
    """
    공식 원두 검색 API
    Args:
        request: 검색어(query)와 정렬 기준(sort_by)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 일치하는 원두의 리스트, 필터 및 정렬 기준 적용 가능.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = BeanSearchInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        beans = Bean.objects.filter(is_official=True).annotate(
            avg_star=ExpressionWrapper(
                Round(Avg("tastedrecord__taste_review__star"), 1),
                output_field=FloatField(),
            ),
            record_count=Count("tastedrecord"),
        )

        filterset = BeanFilter(serializer.validated_data, queryset=beans)
        filtered_beans = filterset.qs

        return get_paginated_response_with_class(request, filtered_beans, BeanSearchSerializer)


@SearchSchema.tastedrecord_search_schema_view
class TastedRecordSearchView(APIView):
    """
    시음 기록 검색 API
    Args:
        request: 검색어(query), 정렬 기준(sort_by), 필터 조건(bean_type, origin_country, min_star, max_star, is_decaf)을 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색 조건과 정렬 기준에 따른 시음 기록 리스트.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = TastedRecordSearchInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        records = (
            TastedRecord.objects.all()
            .select_related("bean", "author", "taste_review")
            .prefetch_related("photo_set")
            .annotate(
                photo_url=Subquery(Photo.objects.filter(tasted_record=OuterRef("pk")).values("photo_url")[:1]),
            )
            .distinct()
        )

        filterset = TastedRecordFilter(serializer.validated_data, queryset=records)
        filtered_records = filterset.qs

        return get_paginated_response_with_class(request, filtered_records, TastedRecordSearchSerializer)


@SearchSchema.post_search_schema_view
class PostSearchView(APIView):
    """
    게시글 검색 API
    Args:
        request: 검색어(query)와 정렬 기준(sort_by)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 일치하는 게시글의 리스트, 정렬 기준 적용 가능.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = PostSearchInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        posts = (
            Post.objects.all()
            .select_related("author")
            .prefetch_related("photo_set")
            .annotate(
                comment_count=Count("comment"),
                photo_url=Subquery(Photo.objects.filter(post=OuterRef("pk")).values("photo_url")[:1]),
            )
            .distinct()
        )

        filterset = PostFilter(serializer.validated_data, queryset=posts)
        filtered_posts = filterset.qs

        return get_paginated_response_with_class(request, filtered_posts, PostSearchSerializer)
