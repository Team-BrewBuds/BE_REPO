from django.urls import path

from .views import ReportAPIView

urlpatterns = [
    path("<str:object_type>/<int:object_id>/", ReportAPIView.as_view(), name="report"),
]
