from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

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

    permission_classes = [IsAuthenticated]  # IsOwnerOrReadOnly 서비스 내에서 처리

    def __init__(self, **kwargs):
        self.comment_service = CommentService()

    def get(self, request, id):
        comment = self.comment_service.get_comment_detail(id)

        response_serializer = CommentOutputSerializer(comment, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        valid_serializer = CommentInputSerializer(data=request.data, context={"request": request}, partial=True)
        valid_serializer.is_valid(raise_exception=True)

        comment = self.comment_service.update_comment(id, request.user, valid_serializer.validated_data)

        response_serializer = CommentOutputSerializer(comment, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        self.comment_service.delete_comment(id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
