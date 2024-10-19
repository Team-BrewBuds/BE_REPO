from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view, OpenApiResponse,
)
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.serializers import PageNumberSerializer
from repo.common.utils import delete, get_object
from repo.common.view_counter import update_view_count
from repo.records.models import Photo
from repo.records.posts.serializers import *
from repo.records.services import get_post_detail, get_post_feed


@extend_schema_view(
    get=extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="subject",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="subject filter",
                enum=[choice[0] for choice in Post.SUBJECT_TYPE_CHOICES],
                examples=[
                    OpenApiExample(
                        name=f"{choice[0]} 조회",
                        summary=f"{choice[0]} 카테고리 게시글 조회",
                        description=f"홈 게시글에서 {choice[0]} 카테고리를 조회합니다.",
                        value=choice[0],
                    )
                    for choice in Post.SUBJECT_TYPE_CHOICES
                ],
            ),
        ],
        responses=PostListSerializer,
        summary="홈 게시글 리스트 조회",
        description="""
            홈 피드의 게시글 list 데이터를 가져옵니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    post=extend_schema(
        request=PostCreateUpdateSerializer,
        responses=PostCreateUpdateSerializer,
        summary="게시글 생성",
        description="""
            단일 게시글을 생성합니다. (사진과 시음기록은 함께 등록할 수 없습니다.)
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
)
class PostListCreateAPIView(APIView):
    """게시글 리스트 조회, 생성 API"""

    def get(self, request):
        subject = request.GET.get("subject")

        if subject not in [choice[0] for choice in Post.SUBJECT_TYPE_CHOICES]:
            subject = "전체"
        subject_mapping = dict(Post.SUBJECT_TYPE_CHOICES)

        subject_value = subject_mapping.get(subject, "all")

        posts = get_post_feed(request.user, subject_value)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        paginated_posts = paginator.paginate_queryset(posts, request)

        serializer = PostListSerializer(paginated_posts, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PostCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                post = Post.objects.create(
                    author=request.user,
                    title=serializer.validated_data["title"],
                    content=serializer.validated_data["content"],
                    subject=serializer.validated_data["subject"],
                    tag=serializer.validated_data["tag"],
                )

                tasted_records = serializer.validated_data.get("tasted_records", [])
                post.tasted_records.set(tasted_records)

                photos = serializer.validated_data.get("photos", [])
                post.photo_set.set(photos)

            return Response(PostCreateUpdateSerializer(post).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    get=extend_schema(
        responses={200: PostDetailSerializer},
        summary="게시글 상세 조회",
        description="""
            게시글의 상세 정보를 가져옵니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    put=extend_schema(
        request=PostCreateUpdateSerializer,
        responses={
            200: PostCreateUpdateSerializer,
            400: OpenApiResponse(description="Bad Request")
        },
        summary="게시글 수정",
        description="""
            게시글의 정보를 수정합니다.
            tasted_record, photo는 id로 수정합니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    patch=extend_schema(
        request=PostCreateUpdateSerializer,
        responses={
            200: PostCreateUpdateSerializer,
            400: OpenApiResponse(description="Bad Request")
        },
        summary="게시글 수정",
        description="""
            게시글의 정보를 수정합니다.
            tasted_record, photo는 id로 수정합니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    delete=extend_schema(
        responses=status.HTTP_204_NO_CONTENT,
        summary="게시글 삭제",
        description="""
            게시글을 삭제합니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
)
class PostDetailApiView(APIView):
    """
    게시글 상세정보 조회, 생성, 수정, 삭제 API
    Args:
        pk

    담당자 : hwstar1204
    """

    def get(self, request, pk):
        _, response = get_object(pk, Post)
        if response:
            return response

        post = get_post_detail(pk)
        instance, response = update_view_count(request, post, Response(), "post_viewed")

        serializer = PostDetailSerializer(instance, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostCreateUpdateSerializer(post, data=request.data, partial=False)

        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                self._update_tasted_records(serializer, post)
                self._update_photos(serializer, post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostCreateUpdateSerializer(post, data=request.data, partial=True)

        if serializer.is_valid():
            with transaction.atomic():
                serializer.save()
                self._update_tasted_records(serializer, post)
                self._update_photos(serializer, post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _update_tasted_records(self, serializer, post):
        tasted_records = serializer.validated_data.get("tasted_records", [])
        post.tasted_records.set(tasted_records)

    def _update_photos(self, serializer, post):
        photos = serializer.validated_data.get("photos", [])
        post.photo_set.set(photos)

    def delete(self, request, pk):
        return delete(request, pk, Post)


class TopSubjectPostsAPIView(APIView):
    """
    홈 [전체] - 주제별 조회수 상위 12개 인기 게시글 조회 API
    Args:
        - subject : 조회할 주제
    Returns:
        - status: 200
    주제 종류 : 일반, 카페, 원두, 정보, 장비, 질문, 고민 (default: 전체)

    담당자 : hwstar1204
    """

    @extend_schema(
        responses=TopPostSerializer,
        summary="인기 게시글 조회",
        description="""
            홈 [전체] - 주제별 조회수 상위 10개 인기 게시글 조회 API
            담당자 : hwstar1204
        """,
        tags=["posts"],
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="subject",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="subject filter",
                enum=[choice[0] for choice in Post.SUBJECT_TYPE_CHOICES],
                examples=[
                    OpenApiExample(
                        name=f"{choice[0]} 조회",
                        summary=f"{choice[0]} 카테고리 인기 게시글 조회",
                        description=f"홈의 인기 게시글에서 {choice[0]} 카테고리를 조회합니다.",
                        value=choice[0],
                    )
                    for choice in Post.SUBJECT_TYPE_CHOICES
                ],
            ),
        ],
    )
    def get(self, request):
        subject = request.GET.get("subject")

        if subject not in [choice[0] for choice in Post.SUBJECT_TYPE_CHOICES]:
            subject = "전체"
        subject_mapping = dict(Post.SUBJECT_TYPE_CHOICES)

        subject_value = subject_mapping.get(subject, "all")

        # TODO 캐시 적용
        posts = Post.objects.get_top_subject_weekly_posts(subject_value)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        paginated_posts = paginator.paginate_queryset(posts, request)

        serializer = TopPostSerializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)
