from django.urls import path

from repo.search.suggest.views import (
    BeanSuggestView,
    BuddySuggestView,
    PostSuggestView,
    TastedRecordSuggestView,
)

urlpatterns = [
    path("buddy/", BuddySuggestView.as_view(), name="buddy"),
    path("bean/", BeanSuggestView.as_view(), name="bean"),
    path("tastedrecord/", TastedRecordSuggestView.as_view(), name="tastedrecord"),
    path("post/", PostSuggestView.as_view(), name="post"),
]
