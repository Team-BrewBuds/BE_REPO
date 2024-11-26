from django.urls import include, path

urlpatterns = [
    path("relationship/", include("repo.interactions.relationship.urls")),
]
