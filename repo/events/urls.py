from django.urls import path

from repo.events.views import (
    EventCompleteAPIView,
    EventDetailAPIView,
    EventListAPIView,
    MyEventCompletionListAPIView,
)

urlpatterns = [
    path("", EventListAPIView.as_view(), name="event-list"),
    path("<uuid:pk>/", EventDetailAPIView.as_view(), name="event-detail"),
    path("<uuid:pk>/complete/", EventCompleteAPIView.as_view(), name="event-complete"),
    path("my-completions/", MyEventCompletionListAPIView.as_view(), name="my-completions"),
]
