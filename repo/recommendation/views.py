import random

import pandas as pd
from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from sklearn.metrics.pairwise import cosine_similarity

from repo.profiles.services import CoffeeLifeCategoryService
from repo.recommendation.loaders import ModelLoader
from repo.recommendation.schemas import BudyRecommendSchema
from repo.recommendation.serializers import (
    BeanRecommendSerializer,
    BudyRecommendSerializer,
)
from repo.recommendation.services import *
from repo.records.models import TastedRecord


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
    유저를 위한 원두 추천 API (모델 기반 추천)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id=None):

        if user_id is None:
            user_id = request.user.id

        high_rated_reviews = (
            TastedRecord.objects.filter(author_id=user_id, taste_review__star__gte=3.5)
            .select_related("bean", "taste_review")
            .order_by("-taste_review__star")[:3]
        )

        if not high_rated_reviews.exists():
            return self.get_random_beans()

        user_taste_data = {
            "avg_acidity": sum([record.taste_review.acidity for record in high_rated_reviews]) / len(high_rated_reviews),
            "avg_body": sum([record.taste_review.body for record in high_rated_reviews]) / len(high_rated_reviews),
            "avg_sweetness": sum([record.taste_review.sweetness for record in high_rated_reviews]) / len(high_rated_reviews),
            "avg_bitterness": sum([record.taste_review.bitterness for record in high_rated_reviews]) / len(high_rated_reviews),
            "combined_flavor": ", ".join([record.taste_review.flavor for record in high_rated_reviews]),
        }

        mlb_encoder = ModelLoader.get_encoder()
        encoded_flavor = pd.DataFrame(mlb_encoder.transform([user_taste_data["combined_flavor"].split(", ")]), columns=mlb_encoder.classes_)

        user_input_final = pd.DataFrame(
            {
                "acidity": [user_taste_data["avg_acidity"]],
                "body": [user_taste_data["avg_body"]],
                "sweetness": [user_taste_data["avg_sweetness"]],
                "bitterness": [user_taste_data["avg_bitterness"]],
            }
        ).join(encoded_flavor)

        recsys_model = ModelLoader.get_model()
        predicted_cluster = recsys_model.predict(user_input_final, size_min=None, size_max=None)[0]

        recsys_data = ModelLoader.get_recsys_data()
        same_cluster_beans = recsys_data[recsys_data["클러스터"] == predicted_cluster]

        similarities = cosine_similarity(user_input_final, same_cluster_beans.drop(columns=["원두 이름", "db_id", "클러스터"]))

        top_10_indices = similarities.argsort()[0][-10:][::-1]
        top_10_beans = same_cluster_beans.iloc[top_10_indices]["db_id"].tolist()
        random.shuffle(top_10_beans)

        recommended_beans = Bean.objects.filter(id__in=top_10_beans).annotate(
            avg_star=Avg("tastedrecord__taste_review__star", default=0), record_cnt=Count("tastedrecord", distinct=True)
        )

        recommended_beans = sorted(recommended_beans, key=lambda bean: top_10_beans.index(bean.id))

        for bean in recommended_beans:
            bean.avg_star = round(bean.avg_star, 1) if bean.avg_star is not None else 0

        serializer = BeanRecommendSerializer(recommended_beans, many=True)
        return Response(serializer.data)

    def get_random_beans(self):
        beans = list(Bean.objects.all())
        random_beans = random.sample(beans, min(len(beans), 10))
        recommended_beans = Bean.objects.filter(id__in=[bean.id for bean in random_beans]).annotate(
            avg_star=Avg("tastedrecord__taste_review__star", default=0), record_cnt=Count("tastedrecord", distinct=True)
        )

        for bean in recommended_beans:
            bean.avg_star = round(bean.avg_star, 1) if bean.avg_star is not None else 0

        serializer = BeanRecommendSerializer(recommended_beans, many=True)
        return Response(serializer.data)
