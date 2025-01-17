from django.urls import path

from .views import ReportAPIView, UserReportAPIView

urlpatterns = [
    path("<str:object_type>/<int:object_id>/", ReportAPIView.as_view(), name="report"),
    path("user/<int:id>/", UserReportAPIView.as_view(), name="user_report"),
]
