from django.urls import path

from repo.records.tasted_record import views

urlpatterns = [
    path("", views.TastedRecordListCreateAPIView.as_view(), name="tasted_record-list-create"),
    path("<int:pk>/", views.TastedRecordDetailApiView.as_view(), name="tasted_record-detail"),
    path("user/<int:id>/", views.UserTastedRecordListView.as_view(), name="user-tasted-records"),
]
