from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord
from repo.search.serializers import (
    BeanSearchSerializer,
    BuddySearchSerializer,
    PostSearchSerializer,
    TastedRecordSearchSerializer,
)


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
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = CustomUser.objects.filter(nickname__icontains=query).values_list("nickname", flat=True).distinct()

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


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
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = Bean.objects.filter(name__icontains=query).values_list("name", flat=True).distinct()

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


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
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = TastedRecord.objects.filter(bean__name__icontains=query).values_list("bean__name", flat=True).distinct()

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


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
        query = request.query_params.get("q", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        suggestions = Post.objects.filter(title__icontains=query).values_list("title", flat=True)

        return Response({"suggestions": list(suggestions)}, status=status.HTTP_200_OK)


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
        query = request.query_params.get("q", "").strip()
        sort_by = request.query_params.get("sort_by", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        users = CustomUser.objects.filter(nickname__icontains=query).annotate(
            record_cnt=Count("tastedrecord"), follower_cnt=Count("relationships_to", filter=Q(relationships_to__relationship_type="follow"))
        )

        if sort_by == "record_cnt":
            users = users.order_by("-record_cnt")
        elif sort_by == "follower_cnt":
            users = users.order_by("-follower_cnt")

        serializer = BuddySearchSerializer(users, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class BeanSearchView(APIView):
    """
    원두 검색 API
    Args:
        request: 검색어(query)와 정렬 기준(sort_by)를 포함한 클라이언트 요청.
    Returns:
        JSON 응답: 검색어와 일치하는 원두의 리스트, 정렬 기준 적용 가능.
    담당자: blakej2432
    """

    def get(self, request):
        query = request.GET.get("q", "").strip()
        sort_by = request.query_params.get("sort_by", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=400)

        beans = Bean.objects.filter(name__icontains=query).annotate(
            avg_star=Avg("tastedrecord__taste_review__star"), record_cnt=Count("tastedrecord")
        )

        if sort_by == "avg_star":
            beans = beans.order_by("-avg_star")
        elif sort_by == "record_cnt":
            beans = beans.order_by("-record_cnt")

        serializer = BeanSearchSerializer(beans, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


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
        query = request.query_params.get("q", "").strip()

        bean_type = request.query_params.get("bean_type", "").strip()
        origin_country = request.query_params.get("origin_country", "").strip()
        min_star = request.query_params.get("min_star", "").strip()
        max_star = request.query_params.get("max_star", "").strip()
        is_decaf = request.query_params.get("is_decaf", "").strip()

        sort_by = request.query_params.get("sort_by", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        records = (
            TastedRecord.objects.filter(
                Q(content__icontains=query)
                | Q(bean__name__icontains=query)
                | Q(tag__icontains=query)
                | Q(taste_review__flavor__icontains=query)
            )
            .select_related("bean", "taste_review")
            .distinct()
        )

        if bean_type:
            records = records.filter(bean__bean_type=bean_type)
        if origin_country:
            records = records.filter(bean__origin_country__icontains=origin_country)
        if min_star:
            records = records.filter(taste_review__star__gte=float(min_star))
        if max_star:
            records = records.filter(taste_review__star__lte=float(max_star))
        if is_decaf:
            records = records.filter(bean__is_decaf=is_decaf)

        if sort_by == "latest":
            records = records.order_by("-created_at")
        elif sort_by == "like_rank":
            records = records.annotate(like_count=Count("like_cnt")).order_by("-like_count")
        elif sort_by == "star_rank":
            records = records.order_by("-taste_review__star")

        serializer = TastedRecordSearchSerializer(records, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


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
        query = request.GET.get("q", "").strip()

        subject = request.GET.get("subject", "").strip()

        sort_by = request.GET.get("sort_by", "").strip()

        if not query:
            return Response({"error": "검색어를 입력해주세요."}, status=400)

        posts = Post.objects.filter(Q(title__icontains=query) | Q(content__icontains=query)).select_related("author").distinct()

        if subject and subject != "전체":
            posts = posts.filter(subject=subject)

        if sort_by == "latest":
            posts = posts.order_by("-created_at")
        elif sort_by == "like_rank":
            posts = posts.annotate(like_count=Count("like_cnt")).order_by("-like_count")

        serializer = PostSearchSerializer(posts, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
