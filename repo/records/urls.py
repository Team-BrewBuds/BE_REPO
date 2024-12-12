from django.urls import include, path

from repo.records import views

urlpatterns = [
    path("post/", include("repo.records.posts.urls")),
    path("tasted_record/", include("repo.records.tasted_record.urls")),
    path("feed/", views.FeedAPIView.as_view(), name="feed"),
    path("comment/", include("repo.records.comment.urls")),
    path("photo/", views.PhotoApiView.as_view(), name="photo-upload"),
    path("photo/profile/", views.ProfilePhotoAPIView.as_view(), name="profile-photo"),
]
