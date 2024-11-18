from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import IsOwnerOrReadOnly
from repo.common.serializers import PageNumberSerializer
from repo.common.utils import get_paginated_response_with_class
from repo.common.view_counter import update_view_count
from repo.records.posts.serializers import *
from repo.records.posts.services import *
from repo.records.services import (
    get_annonymous_posts_feed,
    get_post_detail,
    get_post_feed,
)


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
                required=False,
                examples=[
                    OpenApiExample(
                        name=f"{choice[0]} 조회",
                        summary=f"{choice[0]} 카테고리 게시글 조회",
                        description=f"홈 게시글에서 {choice[0]} 카테고리를 조회합니다.",
                        value=choice[0],
                    )
                    for choice in Post.SUBJECT_TYPE_CHOICES
                ]
                + [
                    OpenApiExample(
                        name="주제 필터 없음",
                        summary="주제 필터 없이 전체 게시글 조회",
                        description="홈 게시글에서 주제 필터 없이 전체 게시글을 조회합니다.",
                        value=None,
                    )
                ],
            ),
        ],
        responses={200: PostListSerializer},
        summary="홈 [게시글] 피드 조회",
        description="""
            홈 피드의 주제별 게시글 list 데이터를 가져옵니다.
            - 순서: 팔로잉, 일반
            - 정렬: 최신순
            - 페이지네이션 적용 (12개)
            - 30분이내 조회하지않은 게시글만 가져옵니다.

            Notice:
            - like_cnt에서 likes로 변경
            - comments(댓글 수), is_user_noted(사용자 저장여부) 추가 됨
            - 비회원일경우 랜덤으로 게시글을 가져옵니다. (subject 쿼리 파라미터 미사용)
            - 주제 (default: 전체)
            : normal(일반), cafe(카페), bean(원두), info(정보), question(질문), worry(고민), gear(장비)


            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    post=extend_schema(
        request=PostCreateUpdateSerializer,
        responses={201: PostDetailSerializer, 400: OpenApiResponse(description="Bad Request")},
        summary="게시글 생성",
        description="""
            단일 게시글을 생성합니다. (사진과 시음기록은 함께 등록할 수 없습니다.)
            태그는 , 로 구분하여 문자열로 요청해주세요.
            로그인한 유저만 게시글 생성 가능
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
)
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
        responses={200: PostCreateUpdateSerializer, 400: OpenApiResponse(description="Bad Request")},
        summary="게시글 수정",
        description="""
            게시글의 정보를 수정합니다.
            tasted_record, photo는 id로 수정합니다.
            notice : 수정 권한은 작성자에게만 허용합니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    patch=extend_schema(
        request=PostCreateUpdateSerializer,
        responses={200: PostCreateUpdateSerializer, 400: OpenApiResponse(description="Bad Request")},
        summary="게시글 수정",
        description="""
            게시글의 정보를 수정합니다.
            tasted_record, photo는 id로 수정합니다.
            notice : 수정 권한은 작성자에게만 허용합니다.
            담당자: hwstar1204
        """,
        tags=["posts"],
    ),
    delete=extend_schema(
        responses={204: OpenApiResponse(description="No Content")},
        summary="게시글 삭제",
        description="""
            게시글을 삭제합니다.
            notice : 삭제 권한은 작성자에게만 허용합니다.
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

    @extend_schema(
        responses={200: TopPostSerializer},
        summary="인기 게시글 조회",
        description="""
            홈 [전체] - 주제별 조회수 상위 60개 인기 게시글 조회 API
            - 정렬: 조회수
            - 페이지네이션 적용

            notice:
            - 필드명 변경 (like_cnt -> likes, comment_cnt -> comments)
            - 필드 추가 (created_at, view_cnt)
            - 차단 유저의 게시글은 제외합니다.
            - 비회원일 경우 예외 처리합니다. (subject 쿼리 파라미터 미사용)
            - 주제 (default: 전체)
            : normal(일반), cafe(카페), bean(원두), info(정보), question(질문), worry(고민), gear(장비)

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
                ]
                + [
                    OpenApiExample(
                        name="주제 필터 없음",
                        summary="주제 필터 없이 전체 게시글 조회",
                        description="홈 게시글에서 주제 필터 없이 전체 게시글을 조회합니다.",
                        value=None,
                    )
                ],
            ),
        ],
    )
    def get(self, request):
        user = request.user  # 비회원 = None
        subject = request.query_params.get("subject")  # 주제 필터 없는 경우 = None

        posts = get_top_subject_weekly_posts(user, subject)
        return get_paginated_response_with_class(request, posts, TopPostSerializer)
