from django.urls import path

from . import views

urlpatterns = [
    path("buddy_suggest/", views.BuddySuggestView.as_view(), name="buddy_suggest"),
    path("bean_suggest/", views.BeanSuggestView.as_view(), name="bean_suggest"),
    path("tastedrecord_suggest/", views.TastedRecordSuggestView.as_view(), name="tastedrecord_suggest"),
    path("post_suggest/", views.PostSuggestView.as_view(), name="post_suggest"),
    path("bean_list/", views.BeanSearchView.as_view(), name="bean_list"),
    path("buddy_list/", views.BuddySearchView.as_view(), name="buddy_list"),
    path("tastedrecord_list/", views.TastedRecordSearchView.as_view(), name="tastedrecord_list"),
    path("post_list/", views.PostSearchView.as_view(), name="post_list"),
]
