from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import IsOwnerOrReadOnly
from repo.common.utils import get_paginated_response_with_class
from repo.records.posts.schemas import PostSchema
from repo.records.posts.serializers import *
from repo.records.posts.services import *


@PostSchema.post_list_create_schema_view
class PostListCreateAPIView(APIView):
    """게시글 리스트 조회, 생성 API"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    def __init__(self, **kwargs):
        self.post_service = get_post_service()

    def get(self, request):
        user = request.user
        subject = request.query_params.get("subject", None)

        if not user.is_authenticated:
            posts = self.post_service.get_record_list_for_anonymous(subject)
            paginator = PageNumberPagination()
            paginated_posts = paginator.paginate_queryset(posts, request)
            return paginator.get_paginated_response(paginated_posts)

        posts = self.post_service.get_record_list_v2(user, subject=subject, request=request)
        return get_paginated_response_with_class(request, posts, PostListSerializer)

    def post(self, request):
        serializer = PostCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        post = self.post_service.create_record(request.user, serializer.validated_data)
        serializer = PostDetailSerializer(post, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@PostSchema.post_detail_schema_view
class PostDetailAPIView(APIView):
    """
    게시글 상세정보 조회, 생성, 수정, 삭제 API
    Args:
        pk

    담당자 : hwstar1204
    """

    permission_classes = [IsOwnerOrReadOnly]

    def __init__(self, **kwargs):
        self.post_service = get_post_service()

    def get_object(self, pk):
        post = get_object_or_404(Post, pk=pk)
        self.check_object_permissions(self.request, post)
        return post

    def get(self, request, pk):
        post = self.get_object(pk)
        post_detail = self.post_service.get_record_detail(request, post.id)

        serializer = PostDetailSerializer(post_detail, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        post = self.get_object(pk)
        serializer = PostCreateUpdateSerializer(post, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        updated_post = self.post_service.update_record(post, serializer.validated_data)
        return Response(PostDetailSerializer(updated_post, context={"request": request}).data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        post = self.get_object(pk)
        serializer = PostCreateUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated_post = self.post_service.update_record(post, serializer.validated_data)
        return Response(PostDetailSerializer(updated_post, context={"request": request}).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        post = self.get_object(pk)
        self.post_service.delete_record(post)
        return Response(status=status.HTTP_204_NO_CONTENT)


@PostSchema.user_post_list_schema_view
class UserPostListAPIView(APIView):
    """특정 사용자의 게시글 조회 API"""

    def __init__(self, **kwargs):
        self.post_service = get_post_service()

    def get(self, request, id):
        subject = request.query_params.get("subject", None)

        posts = self.post_service.get_user_records(id, subject=subject)

        return get_paginated_response_with_class(request, posts, UserPostSerializer)


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

    def __init__(self, **kwargs):
        self.top_post_service = get_top_post_service()

    def get(self, request):
        user = request.user
        subject = request.query_params.get("subject", None)

        posts = self.top_post_service.get_top_posts(subject, user)

        if isinstance(posts, QuerySet):  # 캐싱 서버 연결 실패시 직접 DB 조회
            return get_paginated_response_with_class(request, posts, TopPostSerializer)

        paginator = PageNumberPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        return paginator.get_paginated_response(paginated_posts)
