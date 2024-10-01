from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Post, Tasted_Record
from records.serializers import PageNumberSerializer, CommentSerializer
from records.services import get_comment_list, get_post_or_tasted_record_detail


class LikeApiView(APIView):
    """
    게시글 및 시음기록에 좋아요를 추가하거나 취소하는 API
    Args:
        - object_type : "post" 또는 "tasted_record"
        - object_id : 좋아요를 처리할 객체의 ID
    Returns:
        - status: 200
    """

    def post(self, request):
        user = request.user
        object_type = request.data.get("object_type")
        object_id = request.data.get("object_id")
        # action = request.data.get('action')

        if not object_id or not object_type:
            return Response({"error": "object_id and object_type are required"}, status=status.HTTP_400_BAD_REQUEST)

        if object_type == "post":
            obj = get_object_or_404(Post, pk=object_id)
        else:
            obj = get_object_or_404(Tasted_Record, pk=object_id)

        if user in obj.like_cnt.all():
            obj.like_cnt.remove(user)
        else:
            obj.like_cnt.add(user)

        return Response(status=status.HTTP_200_OK)

class CommentApiView(APIView):
    """
    게시글 및 시음기록에 댓글 생성, 리스트 조회 API
    Args:
        - object_type : "post" 또는 "tasted_record"
        - object_id : 댓글을 처리할 객체의 ID
        - content : 댓글 내용
    Returns:
    - status: 200
    """

    def get(self, request, object_type, object_id):
        page_serializer = PageNumberSerializer(data=request.GET)
        if page_serializer.is_valid():
            page = page_serializer.validated_data["page"]
        else:
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        comments, has_next = get_comment_list(object_type, object_id, page)
        comment_serializer = CommentSerializer(comments, many=True)
        
        return Response({"comments": comment_serializer.data, "has_next": has_next}, status=status.HTTP_200_OK)

    def post(self, request, object_type, object_id):
        user = request.user
        content = request.data.get("content")

        if not content:
            return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

        obj = get_post_or_tasted_record_detail(object_type, object_id)
        obj.comment_set.create(user=user, content=content)

        return Response(status=status.HTTP_200_OK)


class CommentDetailAPIView(APIView):
    """
    댓글 상세정보 수정, 삭제 API
    Args:
        - pk
    Returns:
        - status: 200

    """
    # def put(self, request, pk):
    #     return update(request, pk, Comment, CommentSerializer, False)
    
    # def patch(self, request, pk):
    #     return update(request, pk, Comment, CommentSerializer, True)
    
    # def delete(self, request, pk):
    #     return delete(request, pk, Comment)
    

