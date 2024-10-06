from django.urls import path

from repo.records.posts import views

urlpatterns = [
    path("<int:pk>/", views.PostDetailApiView.as_view(), name="post-detail"),
    path("feed/", views.PostFeedAPIView.as_view(), name="post-feed"),
]
