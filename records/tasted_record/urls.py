from django.urls import path
from records.tasted_record import views
urlpatterns = [
    path('{int:pk}', views.TastedRecordDetailApiView.as_view(), name='tasted-record-detail'),
    path('list', views.TastedRecordListCreateApiView.as_view(), name='tasted-record-list'),
]