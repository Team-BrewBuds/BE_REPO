from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from records.models import Post, Tasted_Record


# Create your views here.
class LikeApiView(APIView):
    """
    게시글 및 시음기록에 좋아요를 추가하거나 취소하는 API
    Args:
        - object_type : "post" 또는 "tasted_record"
        - object_id : 좋아요를 처리할 객체의 ID
    Returns:
    - status: 200
    """

    def post(self, request):
        user = request.user
        object_type = request.data.get("object_type")
        object_id = request.data.get("object_id")
        # action = request.data.get('action')

        if not object_id or not object_type:
            return Response({"error": "object_id and object_type are required"}, status=status.HTTP_400_BAD_REQUEST)

        if object_type == "post":
            obj = get_object_or_404(Post, pk=object_id)
        else:
            obj = get_object_or_404(Tasted_Record, pk=object_id)

        if user in obj.like_cnt.all():
            obj.like_cnt.remove(user)
        else:
            obj.like_cnt.add(user)

        return Response(status=status.HTTP_200_OK)
