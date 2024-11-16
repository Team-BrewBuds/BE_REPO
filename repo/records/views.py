from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.bucket import (
    create_unique_filename,
    delete_photos,
    delete_profile_photo,
)
from repo.common.serializers import (
    ObjectSerializer,
    PhotoDetailSerializer,
    PhotoUpdateSerializer,
    PhotoUploadSerializer,
)
from repo.common.utils import (
    delete,
    get_paginated_response_with_class,
    get_paginated_response_with_func,
    update,
)
from repo.records.models import Comment, Note, Photo, Report
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

    def post(self, request, object_type, object_id):
        user_id = request.user.id
        if not request.user.is_authenticated:
            return Response({"error": "user not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        obj = get_post_or_tasted_record_or_comment(object_type, object_id)

        if user_id in obj.like_cnt.values_list("id", flat=True):
            return Response({"detail": "like already exists"}, status=status.HTTP_409_CONFLICT)

        obj.like_cnt.add(user_id)
        return Response({"detail": "like created"}, status=status.HTTP_201_CREATED)

    def delete(self, request, object_type, object_id):
        user_id = request.user.id
        if not request.user.is_authenticated:
            return Response({"error": "user not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

        obj = get_post_or_tasted_record_or_comment(object_type, object_id)

        if user_id not in obj.like_cnt.values_list("id", flat=True):
            return Response({"detail": "like not found"}, status=status.HTTP_404_NOT_FOUND)

        obj.like_cnt.remove(user_id)
        return Response({"detail": "like deleted"}, status=status.HTTP_204_NO_CONTENT)


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


@PhotoSchema.photo_schema_view
class PhotoApiView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    @transaction.atomic
    def post(self, request):
        """임시 사진 업로드 API"""
        serializer = PhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        files = serializer.validated_data["photo_url"]
        try:
            photos = []  # 업로드할 사진 목록
            for i, file in enumerate(files):
                file.name = create_unique_filename(file.name, is_main=(i == 0))
                photo = Photo(photo_url=file)
                photo.save()
                photos.append(photo)

            return Response(PhotoDetailSerializer(photos, many=True).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            delete_photos(photos)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def put(self, request):
        """사진 수정 API (기존 사진 삭제 후 새로운 사진 업로드)"""
        serializer = PhotoUpdateSerializer(
            data={
                "photo_url": request.FILES.getlist("photo_url"),
                "object_type": request.query_params.get("object_type"),
                "object_id": request.query_params.get("object_id"),
            }
        )
        serializer.is_valid(raise_exception=True)

        files = serializer.validated_data["photo_url"]
        object_type = serializer.validated_data["object_type"]
        object_id = serializer.validated_data["object_id"]

        try:
            obj = get_post_or_tasted_record_detail(object_type, object_id)  # 객체 존재 여부 확인

            if obj.author != request.user:  # 작성자 권한 체크
                return Response({"error": "권한이 없습니다"}, status=status.HTTP_403_FORBIDDEN)

            delete_photos(obj)  # 기존 사진 삭제

            photos = []  # 업로드할 사진 목록
            for i, file in enumerate(files):
                file.name = create_unique_filename(file.name, is_main=(i == 0))
                photo = Photo(**{object_type: obj, "photo_url": file})
                photo.save()
                photos.append(photo)

            return Response(PhotoDetailSerializer(photos, many=True).data, status=status.HTTP_200_OK)
        except ValueError:
            return Response({"error": "invalid object_type"}, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            return Response({"error": "object not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @transaction.atomic
    def delete(self, request):
        """사진 삭제 API"""
        serializer = ObjectSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        object_type = serializer.validated_data["object_type"]
        object_id = serializer.validated_data["object_id"]

        try:
            obj = get_post_or_tasted_record_detail(object_type, object_id)

            if obj.author != request.user:  # 작성자 권한 체크
                return Response({"error": "권한이 없습니다"}, status=status.HTTP_403_FORBIDDEN)

            delete_photos(obj)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError:
            return Response({"error": "invalid object_type"}, status=status.HTTP_400_BAD_REQUEST)
        except Http404:
            return Response({"error": "object not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@ProfilePhotoSchema.profile_photo_schema_view
class ProfilePhotoAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        if "photo_url" not in request.FILES:
            return Response({"error": "photo_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES["photo_url"]
        file.name = create_unique_filename(file.name, is_main=True)

        try:
            # 기존 프로필 이미지가 있다면 삭제
            delete_profile_photo(request.user)

            request.user.profile_image = file
            request.user.save(update_fields=["profile_image"])

            return Response({"profile_image": request.user.profile_image.url}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            delete_profile_photo(request.user)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@ReportSchema.report_schema_view
class ReportApiView(APIView):
    @transaction.atomic
    def post(self, request):
        # 1. 인증 확인
        if not request.user.is_authenticated:
            return Response({"error": "로그인이 필요한 서비스입니다."}, status=status.HTTP_401_UNAUTHORIZED)

        # 2. 중복 신고 확인
        object_type = request.data.get("object_type")
        object_id = request.data.get("object_id")

        if Report.objects.filter(author=request.user, object_type=object_type, object_id=object_id).exists():
            return Response({"message": "이미 신고한 컨텐츠입니다."}, status=status.HTTP_200_OK)

        # 3. 데이터 유효성 검증
        serializer = ReportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # 4. 신고 대상 객체 존재 여부 확인
        try:
            target_object = get_post_or_tasted_record_or_comment(object_type, object_id)
        except Http404:
            return Response({"error": "신고할 컨텐츠가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": f"잘못된 신고 대상 타입입니다: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 5. 신고 생성 및 응답
        report = serializer.save(author=request.user)
        response_data = serializer.data
        response_data["target_author"] = target_object.author.nickname
        return Response(response_data, status=status.HTTP_201_CREATED)
