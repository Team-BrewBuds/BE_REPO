from django.urls import include, path

from repo.search.views import (
    BeanSearchView,
    BuddySearchView,
    PostSearchView,
    TastedRecordSearchView,
)

urlpatterns = [
    path("suggest/", include("repo.search.suggest.urls")),
    path("buddy_list/", BuddySearchView.as_view(), name="buddy_list"),
    path("bean_list/", BeanSearchView.as_view(), name="bean_list"),
    path("tastedrecord_list/", TastedRecordSearchView.as_view(), name="tastedrecord_list"),
    path("post_list/", PostSearchView.as_view(), name="post_list"),
]
