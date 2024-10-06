from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.posts.serializers import PostFeedSerializer, PostDetailSerializer
from records.serializers import PageNumberSerializer
from records.services import get_post_feed2, get_post_detail
from records.models import Post
from common.utils import get_object, create, update, delete
from common.view_counter import update_view_count

class PostFeedAPIView(APIView):
    """
    홈 피드의 게시글 list 데이터를 가져옵니다.
    Returns:
        게시글: 카테고리, 제목, 내용, 조회수, 좋아요 수, 작성일, 선택(사진 or 시음기록)
        프로필: id, 닉네임, 프로필 사진
    담당자 : hwstar1204
    """

    def get(self, request):
        page_serializer = PageNumberSerializer(data=request.GET)
        if page_serializer.is_valid():
            page = page_serializer.validated_data["page"]
        else:
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        posts, has_next = get_post_feed2(request.user, page)
        post_serializer = PostFeedSerializer(posts, many=True)

        return Response({"records": post_serializer.data, "has_next": has_next}, status=status.HTTP_200_OK)


class PostDetailApiView(APIView):
    """
    게시글 상세정보 조회, 생성, 수정, 삭제 API
    Args: 
        pk
    Returns:
        게시글: 제목, 내용, 주제, 조회수, 좋아요 수, 작성일, 선택(사진 or 시음기록)
        프로필: id, 닉네임, 프로필 사진
    담당자 : hwstar1204
    """

    def get(self, request, pk):
        _, response = get_object(pk, Post)
        if response:
            return response
        
        post = get_post_detail(pk)

        instance, response = update_view_count(request, post, Response(), "post_viewed")

        serializer = PostDetailSerializer(instance)
        response.data = serializer.data
        response.status = status.HTTP_200_OK
        return response

    def post(self, request):
        return create(request, PostDetailSerializer)

    def put(self, request, pk):
        return update(request, pk, Post, PostDetailSerializer, False)
    
    def patch(self, request, pk):
        return update(request, pk, Post, PostDetailSerializer, True)
    
    def delete(self, request, pk):
        return delete(request, pk, Post)