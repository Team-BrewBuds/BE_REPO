import random

from django.db.models import Count, Q
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from repo.profiles.models import CustomUser, UserDetail
from repo.recommendation.schemas import BudyRecommendSchema
from repo.recommendation.serializers import BudyRecommendSerializer


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
        user_detail = get_object_or_404(UserDetail, user=user)
        coffee_life_helper = user_detail.get_coffee_life_helper()
        true_categories = coffee_life_helper.get_true_categories()

        if not true_categories:
            category = random.choice(UserDetail.COFFEE_LIFE_CHOICES)
        else:
            category = random.choice(true_categories)

        recommend_user_list = (
            CustomUser.objects.select_related("user_detail")
            .only("user_detail__coffee_life")
            .filter(user_detail__coffee_life__contains={category: True})
            .exclude(id=user.id)
            .annotate(follower_cnt=Count("relationships_to", filter=Q(relationships_to__relationship_type="follow")))
            .order_by("?")[:10]
        )

        serializer = BudyRecommendSerializer(recommend_user_list, many=True)
        response_data = {"users": serializer.data, "category": category}

        return Response(response_data, status=status.HTTP_200_OK)
