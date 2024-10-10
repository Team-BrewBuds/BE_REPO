from django.urls import path

from repo.records.tasted_record import views

urlpatterns = [
    path("<int:pk>/", views.TastedRecordDetailApiView.as_view(), name="tasted-record-detail"),
    path("feed/", views.TastedRecordFeedView.as_view(), name="tasted-record-feed"),
]
