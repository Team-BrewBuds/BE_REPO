from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.serializers import PhotoSerializer
from repo.common.utils import delete, update
from repo.records.models import Comment, Note, Photo, Post, TastedRecord
from repo.records.schemas import *
from repo.records.serializers import CommentSerializer, LikeSerializer, NoteSerializer
from repo.records.services import (
    get_comment,
    get_comment_list,
    get_common_feed,
    get_following_feed,
    get_post_or_tasted_record_detail,
    get_refresh_feed,
    get_serialized_data,
)


@FeedSchema.feed_schema_view
class FeedAPIView(APIView):
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

        serialized_data = get_serialized_data(request, page_obj)

        return Response(
            {
                "results": serialized_data,
                "has_next": page_obj.has_next(),
                "current_page": page_obj.number,
            },
            status=status.HTTP_200_OK,
        )


@LikeSchema.like_schema_view
class LikeApiView(APIView):
    def post(self, request):
        user_id = request.user.id
        serializer = LikeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        object_type = serializer.validated_data["object_type"]
        object_id = serializer.validated_data["object_id"]

        model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}
        model_class = model_map.get(object_type)

        obj = get_object_or_404(model_class, pk=object_id)

        if user_id in obj.like_cnt.values_list("id", flat=True):
            obj.like_cnt.remove(user_id)
            status_code = status.HTTP_200_OK
        else:
            obj.like_cnt.add(user_id)
            status_code = status.HTTP_201_CREATED

        return Response(status=status_code)


# TODO NoteAPI, NoteDetailAPI 통합 가능
@NoteSchema.note_schema_view
class NoteApiView(APIView):
    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        object_type = serializer.validated_data["object_type"]
        object_id = serializer.validated_data["object_id"]

        existing_note = Note.objects.existing_note(user, object_type, object_id)
        if existing_note:
            return Response({"detail": "note already exists"}, status=status.HTTP_200_OK)

        Note.objects.create_note_for_object(user, object_type, object_id)
        return Response({"detail": "note created"}, status=status.HTTP_201_CREATED)


@NoteDetailSchema.note_detail_schema_view
class NoteDetailApiView(APIView):
    def delete(self, request, object_type, object_id):
        user = request.user

        existing_note = Note.objects.existing_note(user, object_type, object_id)
        if existing_note:
            existing_note.delete()
            return Response({"detail": "note deleted"}, status=status.HTTP_200_OK)
        return Response({"detail": "note not found"}, status=status.HTTP_404_NOT_FOUND)


@CommentSchema.comment_schema_view
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
        comments = get_comment_list(object_type, object_id)

        paginator = PageNumberPagination()
        paginator.page_size = 12
        page_obj = paginator.paginate_queryset(comments, request)

        serializer = CommentSerializer(page_obj, many=True)
        return paginator.get_paginated_response(serializer.data)

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


@CommentDetailSchema.comment_detail_schema_view
class CommentDetailAPIView(APIView):
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


@ImageSchema.image_schema_view
class ImageApiView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        files = request.FILES.getlist("photo_url")
        if not files:
            return Response({"error": "photo_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PhotoSerializer(data=[{"photo_url": file} for file in files], many=True)
        if serializer.is_valid():
            photos = serializer.save()
            for photo in photos:
                photo.save()

            data = [{"id": photo.id, "photo_url": photo.photo_url.url} for photo in photos]

            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        photo_ids = request.query_params.getlist("photo_id")
        if not photo_ids:
            return Response({"error": "photo_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        photos = Photo.objects.filter(id__in=photo_ids)
        if not photos.exists():
            return Response({"error": "photo not found"}, status=status.HTTP_404_NOT_FOUND)

        delete_cnt = 0
        try:
            for photo in photos:
                photo.delete()
                delete_cnt += 1
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(f"{delete_cnt} photos deleted successfully", status=status.HTTP_204_NO_CONTENT)
