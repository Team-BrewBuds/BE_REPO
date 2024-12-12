from django.urls import path

from .views import CommentApiView, CommentDetailAPIView

urlpatterns = [
    path("<int:id>/", CommentDetailAPIView.as_view(), name="comment-detail"),
    path("<str:object_type>/<int:object_id>/", CommentApiView.as_view(), name="comment-list"),
]
