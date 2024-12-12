from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .schemas import ReportSchema
from .serializers import ReportSerializer
from .services import ReportService


@ReportSchema.report_schema_view
class ReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        self.report_service = ReportService()

    def post(self, request, object_type, object_id):
        context = {"request": request, "object_type": object_type, "object_id": object_id}
        serializer = ReportSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        reason = serializer.validated_data["reason"]
        report = self.report_service.create(user=request.user, object_type=object_type, object_id=object_id, reason=reason)

        target_author = self.report_service.get_target_author(object_type, object_id)
        report.target_author = target_author

        response_serializer = ReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
