from django.urls import path

from repo.recommendation.views import BeanRecommendAPIView, BudyRecommendAPIView

urlpatterns = [
    path("budy/", BudyRecommendAPIView.as_view(), name="budy-recommend"),
    path("bean/<int:user_id>/", BeanRecommendAPIView.as_view(), name="bean-recommend"),
]
