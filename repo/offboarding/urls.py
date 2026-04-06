from django.urls import path

from repo.offboarding.views import ExportRequestsAPIView

urlpatterns = [
    path("closure/export-requests/", ExportRequestsAPIView.as_view(), name="export-requests"),
]
