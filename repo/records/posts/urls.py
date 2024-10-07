from django.urls import path

from repo.records.posts import views

urlpatterns = [
    path("<int:pk>/", views.PostDetailApiView.as_view(), name="post-detail"),
    path("feed/", views.PostFeedAPIView.as_view(), name="post-feed"),
    path('top/', views.TopSubjectPostsAPIView.as_view(), name="post-top"),
]
