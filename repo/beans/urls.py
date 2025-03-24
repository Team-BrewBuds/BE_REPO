from django.urls import path

from repo.beans.views import *

urlpatterns = [
    path("<int:id>/", BeanDetailView.as_view(), name="bean_detail"),
    path("<int:id>/tasted_records/", BeanTastedRecordView.as_view(), name="bean_tasted_records"),
    path("profile/<int:id>/", UserBeanListAPIView.as_view(), name="user_beans"),
    path("search/", BeanNameSearchView.as_view(), name="bean_search"),
]
