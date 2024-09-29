from django.urls import include, path

from records import views

urlpatterns = [
    path("like", views.LikeApiView.as_view(), name="records-likes"),
    path("post/", include("records.posts.urls")),
    path("tasted_record/", include("records.tasted_record.urls")),
]
