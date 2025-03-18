from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord
from repo.search.suggest.schemas import SuggestSchema
from repo.search.suggest.serializers import *


@SuggestSchema.buddy_suggest_schema_view
class BuddySuggestView(APIView):
    """
    사용자 이름 검색어 12개 추천 API
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

        suggestions = CustomUser.objects.filter(nickname__icontains=query).values_list("nickname", flat=True).distinct()[:12]
        serializer = SuggestSerializer({"suggestions": list(suggestions)})
        return Response(serializer.data, status=status.HTTP_200_OK)


@SuggestSchema.bean_suggest_schema_view
class BeanSuggestView(APIView):
    """
    공식 원두 이름 검색어 12개 추천 API
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

        filters = Q(name__icontains=query) & Q(is_official=True)
        suggestions = Bean.objects.filter(filters).values_list("name", flat=True).distinct()[:12]

        serializer = SuggestSerializer({"suggestions": list(suggestions)})
        return Response(serializer.data, status=status.HTTP_200_OK)


@SuggestSchema.tastedrecord_suggest_schema_view
class TastedRecordSuggestView(APIView):
    """
    시음 기록 검색어 12개 추천 API
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

        suggestions = TastedRecord.objects.filter(bean__name__icontains=query).values_list("bean__name", flat=True).distinct()[:12]

        serializer = SuggestSerializer({"suggestions": list(suggestions)})
        return Response(serializer.data, status=status.HTTP_200_OK)


@SuggestSchema.post_suggest_schema_view
class PostSuggestView(APIView):
    """
    게시글 검색어 12개 추천 API
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

        suggestions = Post.objects.filter(title__icontains=query).values_list("title", flat=True).distinct()[:12]

        serializer = SuggestSerializer({"suggestions": list(suggestions)})
        return Response(serializer.data, status=status.HTTP_200_OK)
