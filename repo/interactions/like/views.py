from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .schemas import LikeSchema
from .services import LikeService


@LikeSchema.like_schema_view
class LikeApiView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, object_type, object_id):
        like_service = LikeService(object_type, object_id)
        like_service.increase_like(request.user.id)
        return Response({"detail": "like created"}, status=status.HTTP_201_CREATED)

    def delete(self, request, object_type, object_id):
        like_service = LikeService(object_type, object_id)
        like_service.decrease_like(request.user.id)
        return Response({"detail": "like deleted"}, status=status.HTTP_204_NO_CONTENT)
