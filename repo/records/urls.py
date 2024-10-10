from django.urls import include, path

from repo.records import views

urlpatterns = [
    path("post/", include("repo.records.posts.urls")),
    path("tasted_record/", include("repo.records.tasted_record.urls")),
    path("feed/follow/", views.FollowFeedAPIView.as_view(), name="feed-follow"),
    path("feed/common/", views.CommonFeedAPIView.as_view(), name="feed-common"),
    path("feed/refresh/", views.RefreshFeedAPIView.as_view(), name="feed-refresh"),
    path("like", views.LikeApiView.as_view(), name="records-likes"),
    path("comment/<int:id>", views.CommentDetailAPIView.as_view(), name="comment-detail"),
    path("comment/<str:object_type>/<int:object_id>", views.CommentApiView.as_view(), name="comment-list"),
    path("note/<int:id>", views.NoteDetailApiView.as_view(), name="note-detail"),
    path("note/<str:object_type>/<int:object_id>", views.NoteApiView.as_view(), name="note-list"),
]
