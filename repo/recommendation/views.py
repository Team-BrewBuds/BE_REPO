import random

from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.profiles.services import CoffeeLifeCategoryService
from repo.recommendation.schemas import BudyRecommendSchema
from repo.recommendation.serializers import (
    BeanRecommendSerializer,
    BudyRecommendSerializer,
)
from repo.recommendation.services import *


@BudyRecommendSchema.budy_recommend_schema_view
class BudyRecommendAPIView(APIView):
    """
    유저의 커피 즐기는 방식 6개 중 한가지 방식에 해당 하는 유저 리스트 반환
    Args:
        request: 클라이언트로부터 받은 요청 객체
    Returns:
        users:
            user: 유저의 커피 생활 방식에 해당 하는 유저 리스트 반환 (10명)
            follower_cnt: 유저의 팔로워 수
        category: 커피 생활 방식
        실패 시: HTTP 404 Not Found

    담당자: hwtar1204
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        coffee_life_category_service = CoffeeLifeCategoryService()

        strategy = BuddyRecommendationStrategy(user, coffee_life_category_service)
        service = RecommendationService(strategy)
        recommend_user_list = service.recommend()

        category = strategy.get_selected_category()

        serializer = BudyRecommendSerializer(recommend_user_list, many=True)
        response_data = {"users": serializer.data, "category": category}

        return Response(response_data, status=status.HTTP_200_OK)


class BeanRecommendAPIView(APIView):
    """
    임시 원두추천
    유저를 위한 원두 추천 API (랜덤 10개)
    """

    def get(self, request, user_id):
        beans = list(Bean.objects.all())
        random_beans = random.sample(beans, min(len(beans), 10))

        recommended_beans = Bean.objects.filter(id__in=[bean.id for bean in random_beans]).annotate(
            avg_star=Avg("tastedrecord__taste_review__star", default=0), record_cnt=Count("tastedrecord", distinct=True)
        )

        for bean in recommended_beans:
            bean.avg_star = round(bean.avg_star, 1) if bean.avg_star is not None else 0

        serializer = BeanRecommendSerializer(recommended_beans, many=True)

        return Response(serializer.data)
