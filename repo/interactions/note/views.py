from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .schemas import NoteSchema
from .serializers import NoteCreateSerializer, NoteResponseSerializer
from .services import NoteService


@NoteSchema.note_schema_view
class NoteApiView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.note_service = NoteService()

    def post(self, request, object_type, object_id):
        path_params = {"object_type": object_type, "object_id": object_id}
        serializer = NoteCreateSerializer(data=path_params)
        serializer.is_valid(raise_exception=True)

        note = self.note_service.create(request.user, object_type, object_id)
        response_serializer = NoteResponseSerializer(note)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, object_type, object_id):
        path_params = {"object_type": object_type, "object_id": object_id}
        serializer = NoteCreateSerializer(data=path_params)
        serializer.is_valid(raise_exception=True)

        self.note_service.delete(request.user, object_type, object_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
