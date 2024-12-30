from django.urls import path

from repo.beans.views import *

urlpatterns = [
    path("search/", BeanNameSearchView.as_view(), name="bean_search"),
    path("profile/<int:id>/", UserBeanListAPIView.as_view(), name="user_beans"),
    path("detail/<int:id>/", BeanDetailView.as_view(), name="bean_detail"),
]
