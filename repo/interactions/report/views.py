from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .schemas import ReportSchema
from .serializers import ContentReportSerializer, UserReportSerializer
from .services import ContentReportService, UserReportService


@ReportSchema.report_schema_view
class ContentReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, object_type, object_id):
        serializer = ContentReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_service = ContentReportService()
        reason = serializer.validated_data["reason"]
        report = report_service.create(user=request.user, object_type=object_type, object_id=object_id, reason=reason)

        report.target_author = report_service.get_target_author(object_type, object_id)

        response_serializer = ContentReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@ReportSchema.user_report_schema_view
class UserReportAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        serializer = UserReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_service = UserReportService()
        reason = serializer.validated_data["reason"]
        report = report_service.create(user=request.user, target_user_id=id, reason=reason)

        response_serializer = UserReportSerializer(report)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
