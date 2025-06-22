import random
from typing import List

import pandas as pd
from django.db.models import Avg, Count, Q, QuerySet
from django.db.models.functions import Round
from sklearn.metrics.pairwise import cosine_similarity

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.recommendation.loaders import ModelLoader
from repo.records.models import TastedRecord


class RecommendationStrategy:
    # 추천 > 버디(유저) 추천 > 커피생활 데이터 기반
    # 추천 > 원두 추천 > 선호 원두 데이터 기반
    def recommend(self):
        raise NotImplementedError


class RecommendationService:
    def __init__(self, strategy: RecommendationStrategy):
        self.strategy = strategy

    def recommend(self) -> list:
        return self.strategy.recommend()


class BuddyRecommendationStrategy(RecommendationStrategy):
    def __init__(self, user, category_service):
        self.user = user
        self.user_coffee_life = user.user_detail.coffee_life
        self.category_service = category_service
        self.selected_category = None

    def recommend(self) -> list[CustomUser]:
        is_ture_category_exists = self.category_service.check_true_categories_by_user(self.user)

        if is_ture_category_exists:
            self.selected_category = self.category_service.get_random_true_category_by_user(self.user)
        else:
            self.selected_category = self.category_service.get_random_category()

        users = (
            CustomUser.objects.select_related("user_detail")
            .only("user_detail__coffee_life")
            .filter(user_detail__coffee_life__contains={self.selected_category: True})
            .exclude(id=self.user.id)
            .annotate(follower_cnt=Count("relationships_to", filter=Q(relationships_to__relationship_type="follow")))
            .order_by("?")[:10]
        )

        return users

    def get_selected_category(self):
        return self.selected_category


class BeanRecommendationStrategy(RecommendationStrategy):

    def __init__(self, user):
        self.user = user

    def recommend(self) -> list[Bean]:
        high_rated_reviews = (
            TastedRecord.objects.filter(author_id=self.user.id, taste_review__star__gte=3.5)
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

        recommended_beans = self._annotate_beans_with_stats(top_10_beans)
        recommended_beans_list = list(recommended_beans)
        recommended_beans_list.sort(key=lambda bean: top_10_beans.index(bean.id))
        return recommended_beans_list

    def get_random_beans(self) -> list[Bean]:
        beans = list(Bean.objects.filter(is_official=True).all())
        random_beans = random.sample(beans, min(len(beans), 10))
        recommended_beans = self._annotate_beans_with_stats([bean.id for bean in random_beans])
        return list(recommended_beans)

    def _annotate_beans_with_stats(self, bean_ids: List[int]) -> QuerySet[Bean]:
        return Bean.objects.filter(id__in=bean_ids).annotate(
            avg_star=Round(Avg("tastedrecord__taste_review__star", default=0), 1), record_cnt=Count("tastedrecord", distinct=True)
        )
