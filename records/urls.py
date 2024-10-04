from django.urls import include, path

from records import views

urlpatterns = [
    path("post/", include("records.posts.urls")),
    path("tasted_record/", include("records.tasted_record.urls")),
    path('feed/', views.FeedAPIView.as_view(), name="feed"),
    path("like", views.LikeApiView.as_view(), name="records-likes"),
    path("comment/<int:id>", views.CommentDetailAPIView.as_view(), name="comment-detail"),
    path("comment/<str:object_type>/<int:object_id>", views.CommentApiView.as_view(), name="comment-list"),
    path("note/<int:id>", views.NoteDetailApiView.as_view(), name="note-detail"), # 조회, 수정, 삭제 
    path("note/<str:object_type>/<int:object_id>", views.NoteApiView.as_view(), name="note-list"),  # 생성(저장), object별로 조회

]
