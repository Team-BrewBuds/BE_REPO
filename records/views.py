from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Post, Tasted_Record, Comment, Note
from records.serializers import PageNumberSerializer, CommentSerializer, NoteSerializer, FeedSerializer
from records.services import get_following_feed, get_common_feed
from records.services import get_comment_list, get_post_or_tasted_record_detail, get_comment

from common.utils import update, delete
from common.view_counter import is_viewed


class FollowFeedAPIView(APIView):
    """
    홈 [전체] - 팔로워들의 게시글+시음기록 리스트를 반환하는 API
    Args:
        - page : 조회할 페이지 번호
    Returns:
        - status: 200

    주의: 
        - 팔로잉하는 사용자들의 기록 우선 노출 (팔로잉 O, 조회 X) (최신순)
    담당자: hwstar1204
    """

    def get(self, request):
        page_serializer = PageNumberSerializer(data=request.GET)
        if page_serializer.is_valid():
            page = page_serializer.validated_data["page"]
        else:
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        feed_items, has_next = get_following_feed(user, page)

        results = []
        for item in feed_items:
            if isinstance(item, Post):
                item_id = "post_id"
            elif isinstance(item, Tasted_Record):
                item_id = "tasted_record_id"
            else:
                continue

            if not is_viewed(request, cookie_name="records_viewed", content_id=item_id):
                results.append(item)

        post_serializer = FeedSerializer(results, many=True)
        return Response({"records": post_serializer.data, "has_next": has_next}, status=status.HTTP_200_OK)


class CommonFeedAPIView(APIView):
    """
    홈 [전체] - 일반 게시글+시음기록 리스트를 반환하는 API
    Args:
        - page : 조회할 페이지 번호
    Returns:
        - status: 200

    주의: 
        - 일반 사용자들의 기록 노출  (팔로잉X, 조회 X) (최신순)
    담당자: hwstar1204
    """

    def get(self, request):
        page_serializer = PageNumberSerializer(data=request.GET)
        if page_serializer.is_valid():
            page = page_serializer.validated_data["page"]
        else:
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        feed_items, has_next = get_common_feed(user, page)

        results = []
        for item in feed_items:
            if isinstance(item, Post):
                item_id = "post_id"
            elif isinstance(item, Tasted_Record):
                item_id = "tasted_record_id"
            else:
                continue

            if not is_viewed(request, cookie_name="records_viewed", content_id=item_id):
                results.append(item)

        post_serializer = FeedSerializer(results, many=True)
        return Response({"records": post_serializer.data, "has_next": has_next}, status=status.HTTP_200_OK)


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

class NoteApiView(APIView):
    """
    게시글, 시음기록, 원두 노트 생성, 조회 API
    Args:
        - object_type : "post" 또는 "tasted_record" 또는 "bean"
        - object_id : 노트를 처리할 객체의 ID
    Returns:
    - status: 200
    담당자: hwstar1204
    """

    def dispatch(self, request, *args, **kwargs):
        id = kwargs.get("object_id")
        type = kwargs.get("object_type")

        if not id or not type:
            return Response({"error": "object_id and object_type are required"}, status=status.HTTP_400_BAD_REQUEST)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, object_type, object_id):
        user = request.user
        notes = Note.custom_objects.get_notes_for_user_and_object(user, object_type, object_id)
        serializer = NoteSerializer(notes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


    def post(self, request, object_type, object_id):
        user = request.user
        note = Note.custom_objects.create_note_for_object(user, object_type, object_id)
        serializer = NoteSerializer(note)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteDetailApiView(APIView):
    """
    노트 상세정보 조회, 삭제 API
    Args:
        - id : 노트 ID
    Returns:
        - status: 200
    담당자: hwstar1204
    """

    def get(self, request, id):
        note = get_object_or_404(Note, pk=id)
        note_serializer = NoteSerializer(note)
        return Response(note_serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, id):
        return delete(request, id, Note)


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
    