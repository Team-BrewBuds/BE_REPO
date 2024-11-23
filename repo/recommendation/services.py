from django.db.models import Count, Q

from repo.beans.models import Bean
from repo.profiles.models import CustomUser


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
        self.preferred_bean_taste_data = user.user_detail.preferred_bean_taste

    def recommend(self) -> list[Bean]:
        # 원두 추천 로직
        pass
