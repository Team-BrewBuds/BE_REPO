from django.urls import path

from repo.recommendation.views import BudyRecommendAPIView

urlpatterns = [
    path("budy/", BudyRecommendAPIView.as_view(), name="budy-recommend"),
]
