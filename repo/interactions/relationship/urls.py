from django.urls import path

from .views import *

urlpatterns = [
    path("follow/", FollowListAPIView.as_view(), name="my_follow_list"),
    path("follow/<int:id>/", FollowListCreateDeleteAPIView.as_view(), name="follow"),
    path("block/", BlockListAPIView.as_view(), name="my_block_list"),
    path("block/<int:id>/", BlockListCreateDeleteAPIView.as_view(), name="block"),
]
