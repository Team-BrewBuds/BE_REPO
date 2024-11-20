from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import IsOwnerOrReadOnly
from repo.common.utils import get_paginated_response_with_class
from repo.common.view_counter import update_view_count
from repo.records.posts.schemas import PostSchema
from repo.records.posts.serializers import *
from repo.records.posts.services import *
from repo.records.services import (
    get_annonymous_posts_feed,
    get_post_detail,
    get_post_feed,
)


@PostSchema.post_list_create_schema_view
class PostListCreateAPIView(APIView):
    """게시글 리스트 조회, 생성 API"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            posts = get_annonymous_posts_feed()
            return get_paginated_response_with_class(request, posts, PostListSerializer)

        subject = request.query_params.get("subject", None)
        posts = get_post_feed(request, user, subject)

        return get_paginated_response_with_class(request, posts, PostListSerializer)

    def post(self, request):
        serializer = PostCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                post = create_post(request.user, serializer.validated_data)
                serializer = PostDetailSerializer(post, context={"request": request})

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@PostSchema.post_detail_schema_view
class PostDetailAPIView(APIView):
    """
    게시글 상세정보 조회, 생성, 수정, 삭제 API
    Args:
        pk

    담당자 : hwstar1204
    """

    permission_classes = [IsOwnerOrReadOnly]

    def get_object(self, pk):
        post = get_object_or_404(Post, pk=pk)
        self.check_object_permissions(self.request, post)
        return post

    def get(self, request, pk):
        post = self.get_object(pk)
        post_detail = get_post_detail(post.id)

        # 쿠키 기반 조회수 업데이트
        response = update_view_count(request, post_detail, Response(), "post_viewed")
        response.data = PostDetailSerializer(post_detail).data
        response.status_code = status.HTTP_200_OK

        return response

    def put(self, request, pk):
        post = self.get_object(pk)
        serializer = PostCreateUpdateSerializer(post, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated_post = update_post(post, serializer.validated_data)
            return Response(PostDetailSerializer(updated_post, context={"request": request}).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        post = self.get_object(pk)
        serializer = PostCreateUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            updated_post = update_post(post, serializer.validated_data)
            return Response(PostDetailSerializer(updated_post, context={"request": request}).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        post = self.get_object(pk)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@PostSchema.top_posts_schema_view
class TopSubjectPostsAPIView(APIView):
    """
    홈 [전체] - 주제별 조회수 상위 12개 인기 게시글 조회 API
    Args:
        - subject : 조회할 주제
    Returns:
        - status: 200
    주제 종류 : 일반, 카페, 원두, 정보, 질문, 고민 (default: 전체)

    담당자 : hwstar1204
    """

    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user  # 비회원 = None
        subject = request.query_params.get("subject")  # 주제 필터 없는 경우 = None

        posts = get_top_subject_weekly_posts(user, subject)
        return get_paginated_response_with_class(request, posts, TopPostSerializer)
