from django.urls import path

from .views import LikeApiView

urlpatterns = [
    path("<str:object_type>/<int:object_id>/", LikeApiView.as_view(), name="records-likes"),
]
