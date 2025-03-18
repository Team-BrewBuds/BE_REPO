from django.urls import include, path

from repo.search.views import *

urlpatterns = [
    path("buddy/", BuddySearchView.as_view(), name="buddy"),
    path("bean/", BeanSearchView.as_view(), name="bean"),
    path("tasted_record/", TastedRecordSearchView.as_view(), name="tasted_record"),
    path("post/", PostSearchView.as_view(), name="post"),
    # 검색어 추천
    path("suggest/", include("repo.search.suggest.urls")),
]
