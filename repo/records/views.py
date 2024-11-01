from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.serializers import PhotoSerializer
from repo.common.utils import (
    delete,
    get_paginated_response_with_class,
    get_paginated_response_with_func,
    update,
)
from repo.records.models import Comment, Note, Photo, Post, TastedRecord
from repo.records.schemas import *
from repo.records.serializers import CommentSerializer, ReportSerializer
from repo.records.services import (
    annonymous_user_feed,
    get_comment,
    get_comment_list,
    get_common_feed,
    get_following_feed,
    get_post_or_tasted_record_detail,
    get_post_or_tasted_record_or_comment,
    get_refresh_feed,
    get_serialized_data,
)


@FeedSchema.feed_schema_view
class FeedAPIView(APIView):
    def get(self, request):
        user = request.user
        if not request.user.is_authenticated:  # AnonymousUser
            queryset = annonymous_user_feed()
            return get_paginated_response_with_func(request, queryset, get_serialized_data)

        feed_type = request.query_params.get("feed_type")
        if feed_type not in ["following", "common", "refresh"]:
            return Response({"error": "invalid feed type"}, status=status.HTTP_400_BAD_REQUEST)

        if feed_type == "following":
            queryset = get_following_feed(request, user)
        elif feed_type == "common":
            queryset = get_common_feed(request, user)
        else:  # refresh
            queryset = get_refresh_feed(user)

        return get_paginated_response_with_func(request, queryset, get_serialized_data)


@LikeSchema.like_schema_view
class LikeApiView(APIView):

    def get_valid_object(self, object_type, object_id):
        model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}
        model_class = model_map.get(object_type)

        if not model_class:
            raise ValueError("Invalid object type.")

        return get_object_or_404(model_class, pk=object_id)

    def post(self, request, object_type, object_id):
        user_id = request.user.id
        if not request.user.is_authenticated:
            return Response({"error": "user not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        obj = self.get_valid_object(object_type, object_id)

        if user_id in obj.like_cnt.values_list("id", flat=True):
            return Response({"detail": "like already exists"}, status=status.HTTP_409_CONFLICT)

        obj.like_cnt.add(user_id)
        return Response({"detail": "like created"}, status=status.HTTP_201_CREATED)

    def delete(self, request, object_type, object_id):
        user_id = request.user.id
        if not request.user.is_authenticated:
            return Response({"error": "user not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        obj = self.get_valid_object(object_type, object_id)

        if user_id not in obj.like_cnt.values_list("id", flat=True):
            return Response({"detail": "like not found"}, status=status.HTTP_404_NOT_FOUND)

        obj.like_cnt.remove(user_id)
        return Response({"detail": "like deleted"}, status=status.HTTP_204_NO_CONTENT)


# TODO NoteAPI, NoteDetailAPI 통합 가능
@NoteSchema.note_schema_view
class NoteApiView(APIView):
    def post(self, request, object_type, object_id):
        user = request.user

        existing_note = Note.objects.existing_note(user, object_type, object_id)
        if existing_note:
            return Response({"detail": "note already exists"}, status=status.HTTP_200_OK)

        Note.objects.create_note_for_object(user, object_type, object_id)
        return Response({"detail": "note created"}, status=status.HTTP_201_CREATED)

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
        user = request.user
        comments = get_comment_list(object_type, object_id, user)

        return get_paginated_response_with_class(request, comments, CommentSerializer)

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


@ReportSchema.report_schema_view
class ReportApiView(APIView):
    @transaction.atomic
    def post(self, request):
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            object_type = serializer.validated_data["object_type"]
            object_id = serializer.validated_data["object_id"]

            target_object = get_post_or_tasted_record_or_comment(object_type, object_id)
            target_aurhor = target_object.author

            serializer.save(author=request.user, object_type=object_type, object_id=object_id, reason=serializer.validated_data["reason"])
            response_data = serializer.data
            response_data["target_author"] = target_aurhor.nickname

            # email send logic (신고사유, 신고 대상 내용, 신고 대상 작성자 정보, 신고자 정보)
            # send_report_email()

            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
