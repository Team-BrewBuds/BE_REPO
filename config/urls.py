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
    # 스키마를 제공하는 엔드포인트
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
