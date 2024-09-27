from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Post
from records.posts.serializers import PostFeedSerializer
from records.serializers import PageNumberSerializer
from records.services import get_post_feed2


class PostFeedAPIView(APIView):
    """
    모든 Post list 데이터를 가져옵니다.
    게시글 : 카테고리, 제목, 내용, 조회수, 좋아요 수, 작성일, 선택(사진 or 시음기록)
    프로필 : id, 닉네임, 프로필 사진
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

    def post(self, request):
        pass


class PostDetailApiView(APIView):
    def get(self, request, pk):
        pass

    def put(self, request, pk):
        pass

    def delete(self, request, pk):
        pass
