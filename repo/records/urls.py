from django.urls import include, path

from repo.records import views

urlpatterns = [
    path("post/", include("repo.records.posts.urls")),
    path("tasted_record/", include("repo.records.tasted_record.urls")),
    path("feed/", views.FeedAPIView.as_view(), name="feed"),
    path("like/<str:object_type>/<int:object_id>/", views.LikeApiView.as_view(), name="records-likes"),
    path("comment/<int:id>", views.CommentDetailAPIView.as_view(), name="comment-detail"),
    path("comment/<str:object_type>/<int:object_id>", views.CommentApiView.as_view(), name="comment-list"),
    path("note/<str:object_type>/<int:object_id>/", views.NoteApiView.as_view(), name="note"),
    path("photo/<str:object_type>/<int:object_id>/", views.PhotoApiView.as_view(), name="photo-upload"),  # 이미지 업로드 테스트용
    path("report/", views.ReportApiView.as_view(), name="report"),
]
