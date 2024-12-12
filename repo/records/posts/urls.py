from django.urls import path

from repo.records.posts import views

urlpatterns = [
    path("", views.PostListCreateAPIView.as_view(), name="post-list-create"),
    path("<int:pk>/", views.PostDetailAPIView.as_view(), name="post-detail"),
    path("user/<int:id>/", views.UserPostListAPIView.as_view(), name="user-post-list"),
    path("top/", views.TopSubjectPostsAPIView.as_view(), name="post-top"),
]
