from django.urls import include, path

from records import views
# object_type, object_id
urlpatterns = [
    path("<str:object_type>/<int:object_id>/comment/", views.CommentApiView.as_view(), name="comment-list"),
    # path("<str:object_type>/<int:object_id>/comment/>/<int:id>", views.CommentDetailAPIView.as_view(), name="comment-detail"),

    path("like", views.LikeApiView.as_view(), name="records-likes"),
    path("post/", include("records.posts.urls")),
    path("tasted_record/", include("records.tasted_record.urls")),
]
