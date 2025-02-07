from django.core.cache import cache
from django.db import transaction
from django.http import Http404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
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
    get_paginated_response_with_class,
    get_post_or_tasted_record_detail,
)
from repo.records.models import Photo
from repo.records.schemas import *
from repo.records.serializers import FeedSerializer
from repo.records.services import get_feed_service


@FeedSchema.feed_schema_view
class FeedAPIView(APIView):

    def __init__(self, **kwargs):
        self.feed_service = get_feed_service()

    def get(self, request):
        user = request.user
        serializer_class = FeedSerializer

        if not request.user.is_authenticated:  # 비회원
            feed_data = self.feed_service.get_anonymous_feed()
            paginator = PageNumberPagination()
            paginated_queryset = paginator.paginate_queryset(feed_data, request)
            return paginator.get_paginated_response(paginated_queryset)

        feed_type = request.query_params.get("feed_type")
        if feed_type not in ["following", "common", "refresh"]:
            return Response({"error": "invalid feed type"}, status=status.HTTP_400_BAD_REQUEST)

        if feed_type == "following":
            queryset = self.feed_service.get_following_feed(request, user)
        elif feed_type == "common":
            queryset = self.feed_service.get_common_feed(request, user)
        else:  # refresh
            queryset = self.feed_service.get_refresh_feed(user)

        return get_paginated_response_with_class(request, queryset, serializer_class)


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
        serializer = PhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data["photo_url"][0]
        file.name = create_unique_filename(file.name, is_main=True)

        try:
            # 기존 프로필 이미지가 있다면 삭제
            delete_profile_photo(request.user)

            request.user.profile_image = file
            request.user.save(update_fields=["profile_image"])

            return Response({"photo_url": request.user.profile_image.url}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            delete_profile_photo(request.user)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
