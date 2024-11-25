from django.urls import path

from .views import *

urlpatterns = [
    path("follow/", FollowListAPIView.as_view(), name="my_follow_list"),
    path("<int:id>/follow/", FollowListCreateDeleteAPIView.as_view(), name="follow"),
    path("block/", BlockListAPIView.as_view(), name="my_block_list"),
    path("<int:id>/block/", BlockListCreateDeleteAPIView.as_view(), name="block"),
]
