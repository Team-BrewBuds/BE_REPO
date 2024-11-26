from django.urls import path

from . import views

urlpatterns = [
    path("<str:object_type>/<int:object_id>/", views.NoteApiView.as_view(), name="note"),
]
