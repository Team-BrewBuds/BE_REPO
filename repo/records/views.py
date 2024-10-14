from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.utils import delete, update
from repo.records.models import Comment, Note, Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.serializers import (
    CommentSerializer,
    NoteSerializer,
)
from repo.common.serializers import PageNumberSerializer
from repo.records.services import (
    get_comment,
    get_comment_list,
    get_common_feed,
    get_following_feed,
    get_post_or_tasted_record_detail, get_refresh_feed, get_serialized_data,
)
from repo.records.tasted_record.serializers import TastedRecordListSerializer

class FeedAPIView(APIView):
    @extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="feed_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="feed type",
                enum=["following", "common", "refresh"],
            ),
        ],
        responses=[TastedRecordListSerializer, PostListSerializer],
        summary="홈 [전체] 피드",
        description="""
            following:
            홈 [전체] 사용자가 팔로잉한 유저들의 1시간 이내 작성한 시음기록과 게시글을 랜덤순으로 가져오는 함수
            30분이내 조회한 기록, 프라이빗한 시음기록은 제외
            
            common:
            홈 [전체] 일반 시음기록과 게시글을 최신순으로 가져오는 함수
            30분이내 조회한 기록, 프라이빗한 시음기록은 제외
            
            refresh:
            홈 [전체] 시음기록과 게시글을 랜덤순으로 반환하는 API
            프라이빗한 시음기록은 제외
            
            response:
            TastedRecordListSerializer or PostListSerializer
            (아래 Schemas 참조)
        
            담당자 : hwstar1204
        """,
        tags=["Feed"],
    )
    def get(self, request):
        feed_type = request.query_params.get("feed_type")
        if feed_type not in ["following", "common", "refresh"]:
            return Response({"error": "invalid feed type"}, status=status.HTTP_400_BAD_REQUEST)

        page_serializer = PageNumberSerializer(data=request.GET)
        if not page_serializer.is_valid():
            return Response(page_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        page = page_serializer.validated_data["page"]

        if feed_type == "following":
            data = get_following_feed(request, user)
        elif feed_type == "common":
            data = get_common_feed(request, user)
        else:  # refresh
            data = get_refresh_feed()

        paginator = Paginator(data, 12)
        page_obj = paginator.get_page(page)

        serialized_data = get_serialized_data(page_obj)

        return Response({
            "results": serialized_data,
            "has_next": page_obj.has_next(),
            "current_page": page_obj.number,
        }, status=status.HTTP_200_OK)


class LikeApiView(APIView):
    """
    게시글 및 시음기록에 좋아요를 추가하거나 취소하는 API
    Args:
        - object_type : "post" or "TastedRecord" or "comment"
        - object_id : 좋아요를 처리할 객체의 ID
    Returns:
        - status: 200

    담당자: hwstar1204
    """

    def post(self, request):
        user = request.user
        object_type = request.data.get("object_type")
        object_id = request.data.get("object_id")

        model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}

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
        - object_type : "post" 또는 "TastedRecord" 또는 "bean"
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
        - object_type : "post" 또는 "TastedRecord"
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
            - object_type : "post" 또는 "TastedRecord"
            - object_id : 댓글을 처리할 객체의 ID
            - content : 댓글 내용
            - parent_id : 대댓글인 경우 부모 댓글의 ID
        Returns:
            - status: 200

        담당자: hwstar1204
        """
        user = request.user
        content = request.data.get("content")
        parent = request.data.get("parent")

        if not content:
            return Response({"error": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

        obj = get_post_or_tasted_record_detail(object_type, object_id)

        parent_comment = get_comment(parent) if parent else None

        comment_data = {
            "author": user,
            "content": content,
            "parent": parent_comment,
            "post": obj if object_type == "post" else None,
            "tasted_record": obj if object_type == "tasted_record" else None,
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
        comment = get_object_or_404(Comment, pk=id)

        if comment.parent is None:  # soft delete
            comment.is_deleted = True
            comment.content = "삭제된 댓글입니다."
            comment.save()
            return Response(status=status.HTTP_200_OK)

        return delete(request, id, Comment)
