from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Post, Tasted_Record, Comment
from records.serializers import PageNumberSerializer, CommentSerializer
from records.services import get_comment_list, get_post_or_tasted_record_detail, get_comment
from common.utils import update, delete


class LikeApiView(APIView):
    """
    게시글 및 시음기록에 좋아요를 추가하거나 취소하는 API
    Args:
        - object_type : "post" or "tasted_record" or "comment"
        - object_id : 좋아요를 처리할 객체의 ID
    Returns:
        - status: 200
    담당자: hwstar1204
    """

    def post(self, request):
        user = request.user
        object_type = request.data.get("object_type")
        object_id = request.data.get("object_id") 

        model_map = {
            "post": Post,
            "tasted_record": Tasted_Record,
            "comment": Comment
        }

        if not object_id or not object_type:
            return Response({"error": "object_id and object_type are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        model_class = model_map.get(object_type.lower())
        if not model_class:
            return Response({"error": "invalid object_type"}, status=status.HTTP_400_BAD_REQUEST)
        
        obj = get_object_or_404(model_class, pk=object_id)
        
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

    주의:
    - 댓글 생성시 content 필수
    - 대댓글 생성시 parent_id 필수
    담당자: hwstar1204
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
        """
        댓글, 대댓글 생성 API
        Args:
            - object_type : "post" 또는 "tasted_record"
            - object_id : 댓글을 처리할 객체의 ID
            - content : 댓글 내용
            - parent_id : 대댓글인 경우 부모 댓글의 ID
        Returns:
            - status: 200
        담당자: hwstar1204
        """
        user = request.user
        content = request.data.get("content")
        parent_id = request.data.get("parent_id")

        if not content:
            return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

        obj = get_post_or_tasted_record_detail(object_type, object_id)

        parent_comment = get_comment(parent_id) if parent_id else None
        
        comment_data = {
            "user": user,
            "content": content,
            "parent_id": parent_comment,
            "post": obj if object_type == "post" else None,
            "tasted_record": obj if object_type == "tasted_record" else None
        }

        Comment.objects.create(**comment_data)

        return Response(status=status.HTTP_200_OK)


class CommentDetailAPIView(APIView):
    """
    댓글 상세정보 조회, 수정, 삭제 API
    Args:
        - id : 댓글 ID
    Returns:
        - status: 200
    담당자: hwstar1204
    """

    def get(self, request, id):
        comment = get_comment(id)
        comment_serializer = CommentSerializer(comment)
        return Response(comment_serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        return update(request, id, Comment, CommentSerializer, False)
    
    def patch(self, request, id):
        return update(request, id, Comment, CommentSerializer, True)

    def delete(self, request, id):
        commnet = get_object_or_404(Comment, pk=id)

        if commnet.parent_id is None:  # soft delete
            commnet.is_deleted = True
            commnet.content = "삭제된 댓글입니다."
            commnet.save()
            return Response(status=status.HTTP_200_OK)
    
        return delete(request, id, Comment)
    