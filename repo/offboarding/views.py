import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.offboarding.models import EXPORT_REQUEST_DEADLINE, ExportRequest
from repo.offboarding.serializers import (
    ExportRequestCreateSerializer,
    ExportRequestSerializer,
)


class ExportRequestsAPIView(APIView):
    """
    서비스 종료로 인한 사용자 게시글, 시음기록 데이터를 전달받을 이메일 신청 API
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """본인의 이메일 신청 내역 조회"""
        try:
            export_request = ExportRequest.objects.get(user=request.user)
        except ExportRequest.DoesNotExist:
            return Response({"detail": "신청 내역이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExportRequestSerializer(export_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """이메일 신청 (최초 1회)"""
        if datetime.date.today() > EXPORT_REQUEST_DEADLINE:
            return Response({"detail": "신청 기간이 마감되었습니다."}, status=status.HTTP_410_GONE)

        if ExportRequest.objects.filter(user=request.user).exists():
            return Response({"detail": "이미 신청한 내역이 있습니다."}, status=status.HTTP_409_CONFLICT)

        serializer = ExportRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(ExportRequestSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def put(self, request):
        """신청 이메일 수정"""
        try:
            export_request = ExportRequest.objects.get(user=request.user)
        except ExportRequest.DoesNotExist:
            return Response({"detail": "신청 내역이 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExportRequestCreateSerializer(export_request, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ExportRequestSerializer(serializer.instance).data, status=status.HTTP_200_OK)
