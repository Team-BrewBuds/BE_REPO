from django.urls import path

from repo.beans.views import *

urlpatterns = [
    path("search/", BeanNameSearchView.as_view(), name="bean_search"),
    path("<int:id>/beans/", UserBeanListAPIView.as_view(), name="user_beans"),
]
