from django.urls import path

from .views import ContentReportAPIView, UserReportAPIView

urlpatterns = [
    path("<str:object_type>/<int:object_id>/", ContentReportAPIView.as_view(), name="content_report"),
    path("<int:id>/user/", UserReportAPIView.as_view(), name="user_report"),
]
