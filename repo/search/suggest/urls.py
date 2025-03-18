from django.urls import path

from repo.search.suggest.views import *

urlpatterns = [
    path("buddy/", BuddySuggestView.as_view(), name="buddy"),
    path("bean/", BeanSuggestView.as_view(), name="bean"),
    path("tasted_record/", TastedRecordSuggestView.as_view(), name="tasted_record"),
    path("post/", PostSuggestView.as_view(), name="post"),
]
