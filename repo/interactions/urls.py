from django.urls import include, path

urlpatterns = [
    path("relationship/", include("repo.interactions.relationship.urls")),
    path("note/", include("repo.interactions.note.urls")),
    path("report/", include("repo.interactions.report.urls")),
    path("like/", include("repo.interactions.like.urls")),
]
