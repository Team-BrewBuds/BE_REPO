from datetime import datetime
from io import BytesIO

import pandas as pd
from django.db.models import Min, OuterRef, Q, Subquery
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.interactions.note.models import Note
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord

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


# @ReportSchema.admin_report_schema_view
class AdminReportListAPIView(APIView):
    # permission_classes = [IsAdminUser]

    def make_date_format(self, date):
        return date.strftime("%Y-%m-%d %H:%M:%S")

    def get_second_record_subquery(self, model: Post | TastedRecord):
        return Subquery(model.objects.filter(author=OuterRef("id")).order_by("created_at").values("created_at")[1:2])

    def get_first_note_subquery(self, model: Note, noted_model: str):
        filters = Q(author=OuterRef("id")) & Q(**{f"{noted_model}__isnull": False})
        return Subquery(model.objects.filter(filters).order_by("created_at").values("created_at")[:1])

    def get(self, request):
        users = CustomUser.objects.annotate(
            first_tr_at=Min("tastedrecord__created_at"),
            first_post_at=Min("post__created_at"),
            second_tr_at=self.get_second_record_subquery(TastedRecord),
            second_post_at=self.get_second_record_subquery(Post),
            first_noted_tr_at=self.get_first_note_subquery(Note, "tasted_record"),
            first_noted_post_at=self.get_first_note_subquery(Note, "post"),
            first_noted_bean_at=self.get_first_note_subquery(Note, "bean"),
        ).values(
            "id",
            "nickname",
            "created_at",
            "first_tr_at",
            "first_post_at",
            "second_tr_at",
            "second_post_at",
            "first_noted_tr_at",
            "first_noted_post_at",
            "first_noted_bean_at",
        )

        report_list = []
        for user in users:
            report_list.append(
                {
                    "ID": user["id"],
                    "닉네임": user["nickname"],
                    "가입일": self.make_date_format(user["created_at"]) if user["created_at"] else None,
                    "첫 시음기록 작성일": (self.make_date_format(user["first_tr_at"]) if user["first_tr_at"] else None),
                    "두번째 시음기록 작성일": (self.make_date_format(user["second_tr_at"]) if user["second_tr_at"] else None),
                    "첫 게시물 작성일": self.make_date_format(user["first_post_at"]) if user["first_post_at"] else None,
                    "두번째 게시물 작성일": (self.make_date_format(user["second_post_at"]) if user["second_post_at"] else None),
                    "첫 시음기록 저장일": (self.make_date_format(user["first_noted_tr_at"]) if user["first_noted_tr_at"] else None),
                    "첫 게시물 저장일": self.make_date_format(user["first_noted_post_at"]) if user["first_noted_post_at"] else None,
                    "첫 원두 정보 저장일": self.make_date_format(user["first_noted_bean_at"]) if user["first_noted_bean_at"] else None,
                }
            )

        df = pd.DataFrame(report_list)

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Admin_Report_{now}.xlsx"

        excel_file = BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)

        response = HttpResponse(excel_file.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
