from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.common.permissions import IsOwnerOrReadOnly
from repo.common.utils import get_paginated_response_with_class

from .schemas import CommentDetailSchema, CommentSchema
from .serializers import CommentInputSerializer, CommentOutputSerializer
from .services import CommentService


@CommentSchema.comment_schema_view
class CommentApiView(APIView):
    """
    게시글 및 시음기록에 댓글 생성, 리스트 조회 API

    주의:
    - 댓글 생성시 content 필수
    - 대댓글 생성시 parent_id 필수

    담당자: hwstar1204
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, object_type, object_id):
        comment_service = CommentService(object_type, object_id)
        comments = comment_service.get_comment_list(request.user)

        return get_paginated_response_with_class(request, comments, CommentOutputSerializer)

    def post(self, request, object_type, object_id):
        valid_serializer = CommentInputSerializer(data=request.data, context={"request": request})
        valid_serializer.is_valid(raise_exception=True)

        comment_service = CommentService(object_type, object_id)
        comment = comment_service.create_comment(request.user, valid_serializer.validated_data)

        response_serializer = CommentOutputSerializer(comment)
        return Response(response_serializer.data, status=status.HTTP_200_OK)


@CommentDetailSchema.comment_detail_schema_view
class CommentDetailAPIView(APIView):
    """
    댓글 상세 API

    담당자: hwstar1204
    """

    permission_classes = [IsOwnerOrReadOnly]

    def __init__(self, **kwargs):
        self.comment_service = CommentService()

    def get_object(self, pk):
        comment = self.comment_service.get_comment_by_id(pk)
        self.check_object_permissions(self.request, comment)
        return comment

    def get(self, request, id):
        comment = self.comment_service.get_comment_detail(self.get_object(id))

        response_serializer = CommentOutputSerializer(comment, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        valid_serializer = CommentInputSerializer(data=request.data, context={"request": request}, partial=True)
        valid_serializer.is_valid(raise_exception=True)

        comment = self.get_object(id)
        comment = self.comment_service.update_comment(comment, valid_serializer.validated_data)

        response_serializer = CommentOutputSerializer(comment, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        comment = self.get_object(id)
        self.comment_service.delete_comment(comment)
        return Response(status=status.HTTP_204_NO_CONTENT)
