from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord
from repo.search.schemas import SearchSchema, SuggestSchema
from repo.search.serializers import *


@SuggestSchema.buddy_suggest_schema_view
class BuddySuggestView(APIView):
    """
    사용자 이름 검색어 추천 API
    Args:
        request: 검색어(query)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 부분 일치하는 사용자 닉네임 추천 리스트.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = BuddySuggestInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = data["q"]

        suggestions = CustomUser.objects.filter(nickname__icontains=query).values_list("nickname", flat=True).distinct()

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


@SuggestSchema.bean_suggest_schema_view
class BeanSuggestView(APIView):
    """
    원두 이름 검색어 추천 API
    Args:
        request: 검색어(query)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 부분 일치하는 원두 이름 추천 리스트.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = BeanSuggestInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = data["q"]

        suggestions = Bean.objects.filter(name__icontains=query).values_list("name", flat=True).distinct()

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


@SuggestSchema.tastedrecord_suggest_schema_view
class TastedRecordSuggestView(APIView):
    """
    시음 기록 검색어 추천 API
    Args:
        request: 검색어(query)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 부분 일치하는 원두 이름 추천 리스트.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = TastedRecordSuggestInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = data["q"]

        suggestions = TastedRecord.objects.filter(bean__name__icontains=query).values_list("bean__name", flat=True).distinct()

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


@SuggestSchema.post_suggest_schema_view
class PostSuggestView(APIView):
    """
    게시글 검색어 추천 API
    Args:
        request: 검색어(query)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 부분 일치하는 게시글 제목 추천 리스트.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = PostSuggestInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = data["q"]

        suggestions = Post.objects.filter(title__icontains=query).values_list("title", flat=True)

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


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
        data = serializer.validated_data

        query = data["q"]

        users = CustomUser.objects.filter(nickname__icontains=query).annotate(
            record_cnt=Count("tastedrecord"), follower_cnt=Count("relationships_to", filter=Q(relationships_to__relationship_type="follow"))
        )

        if sort_by := data.get("sort_by"):
            if sort_by == "record_cnt":
                users = users.order_by("-record_cnt")
            elif sort_by == "follower_cnt":
                users = users.order_by("-follower_cnt")

        serializer = BuddySearchSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        data = serializer.validated_data

        base_filters = Q(name__icontains=data["q"]) & Q(is_official=True)

        if bean_type := data.get("bean_type"):
            base_filters &= Q(bean_type=bean_type)
        if origin_country := data.get("origin_country"):
            base_filters &= Q(origin_country=origin_country)
        if is_decaf := data.get("is_decaf"):
            base_filters &= Q(is_decaf=is_decaf)
        if min_star := data.get("min_star"):
            base_filters &= Q(avg_star__gte=float(min_star))
        if max_star := data.get("max_star"):
            base_filters &= Q(avg_star__lte=float(max_star))

        beans = Bean.objects.filter(base_filters).annotate(avg_star=Avg("tastedrecord__taste_review__star"))

        stats = (
            TastedRecord.objects.filter(bean__in=beans)
            .values("bean__id")
            .annotate(
                avg_star=Avg("taste_review__star"),
                record_count=Count("id"),
            )
        )
        stats_dict = {stat["bean__id"]: stat for stat in stats}

        if data.get("sort_by"):
            if data["sort_by"] == "avg_star":
                beans = beans.order_by("-avg_star")
            elif data["sort_by"] == "record_count":
                beans = sorted(beans, key=lambda bean: stats_dict.get(bean.id, {}).get("record_count", 0), reverse=True)

        serializer = BeanSearchSerializer(beans, many=True, context={"stats_dict": stats_dict})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        data = serializer.validated_data

        query = data["q"]
        base_filters = (
            Q(content__icontains=query)
            | Q(bean__name__icontains=query)
            | Q(tag__icontains=query)
            | Q(taste_review__flavor__icontains=query)
        )

        records = TastedRecord.objects.filter(base_filters).select_related("bean", "author", "taste_review").distinct()

        if bean_type := data.get("bean_type"):
            base_filters &= Q(bean__bean_type=bean_type)
        if origin_country := data.get("origin_country"):
            base_filters &= Q(bean__origin_country__icontains=origin_country)
        if min_star := data.get("min_star"):
            base_filters &= Q(taste_review__star__gte=float(min_star))
        if max_star := data.get("max_star"):
            base_filters &= Q(taste_review__star__lte=float(max_star))
        if is_decaf := data.get("is_decaf"):
            base_filters &= Q(bean__is_decaf=is_decaf)

        if sort_by := data.get("sort_by"):
            if sort_by == "latest":
                records = records.order_by("-created_at")
            elif sort_by == "like_rank":
                records = records.annotate(like_count=Count("like_cnt")).order_by("-like_count")
            elif sort_by == "star_rank":
                records = records.order_by("-taste_review__star")

        serializer = TastedRecordSearchSerializer(records, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


@SearchSchema.post_search_schema_view
class PostSearchView(APIView):
    """
    게시글 검색 API
    Args:
        request: 검색어(query), 정렬 기준(sort_by), 필터 조건(subject)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색 조건과 정렬 기준에 따른 게시글 리스트.
    담당자: blakej2432
    """

    def get(self, request):
        serializer = PostSearchInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        query = data["q"]
        base_filters = Q(title__icontains=query) | Q(content__icontains=query)

        posts = Post.objects.filter(base_filters).select_related("author").distinct()

        if subject := data.get("subject"):
            base_filters &= Q(subject=subject)

        if sort_by := data.get("sort_by"):
            if sort_by == "latest":
                posts = posts.order_by("-created_at")
            elif sort_by == "like_rank":
                posts = posts.annotate(like_count=Count("like_cnt")).order_by("-like_count")

        serializer = PostSearchSerializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
