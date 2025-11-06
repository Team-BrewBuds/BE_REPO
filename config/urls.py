from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("beans/", include("repo.beans.urls")),
    path("profiles/", include("repo.profiles.urls")),
    path("records/", include("repo.records.urls")),
    path("search/", include("repo.search.urls")),
    path("events/", include("repo.events.urls")),
    # 스키마를 제공하는 엔드포인트
    path("recommendation/", include("repo.recommendation.urls")),
    path("interactions/", include("repo.interactions.urls")),
    path("notifications/", include("repo.notifications.urls")),
    # def-spectacular
    path("api/v1/schema/spectacular/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/spectacular/", SpectacularSwaggerView.as_view(url_name="schema")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
