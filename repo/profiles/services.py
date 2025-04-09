import random

from django.db import transaction
from django.db.models import Count, F, QuerySet, Value
from rest_framework.generics import get_object_or_404

from repo.interactions.relationship.services import RelationshipService
from repo.profiles.models import CustomUser, UserDetail


class UserService:
    def __init__(self):
        self.relationship_repo = RelationshipService()

    def check_user_exists(self, id: int) -> bool:
        """유저 존재 여부 확인"""
        return CustomUser.objects.filter(id=id).exists()

    def get_user_by_id(self, id: int) -> CustomUser:
        """유저 조회"""
        return get_object_or_404(CustomUser, id=id)

    def get_user_profile(self, user: CustomUser) -> dict:
        """유저 프로필 조회"""
        queryset = self.get_profile_base_queryset(user.id)
        return queryset.filter(id=user.id).first()

    def get_other_user_profile(self, user_id: int, other_user_id: int) -> dict:
        """다른 유저 프로필 조회"""
        is_user_following = self.relationship_repo.check_relationship(user_id, other_user_id, "follow")
        is_user_blocking = self.relationship_repo.check_relationship(user_id, other_user_id, "block")

        base_queryset = self.get_profile_base_queryset(user_id)
        return (
            base_queryset.filter(id=other_user_id)
            .annotate(
                is_user_following=Value(is_user_following),
                is_user_blocking=Value(is_user_blocking),
            )
            .first()
        )

    def get_profile_base_queryset(self, id: int) -> QuerySet:
        """유저 프로필 기본 쿼리셋 조회"""
        follower_cnt = self.relationship_repo.get_followers(id).count()
        following_cnt = self.relationship_repo.get_following(id).count()

        return CustomUser.objects.select_related("user_detail").annotate(
            introduction=F("user_detail__introduction"),
            profile_link=F("user_detail__profile_link"),
            coffee_life=F("user_detail__coffee_life"),
            preferred_bean_taste=F("user_detail__preferred_bean_taste"),
            is_certificated=F("user_detail__is_certificated"),
            following_cnt=Value(following_cnt),
            follower_cnt=Value(follower_cnt),
            post_cnt=Count("post"),
        )

    @transaction.atomic
    def update_user(self, user: CustomUser, validated_data: dict) -> CustomUser:
        """유저 정보를 업데이트"""
        if nickname := validated_data.get("nickname"):
            user.nickname = nickname

        if user_detail_data := validated_data.get("user_detail"):
            self._update_user_detail(user, user_detail_data)

        user.save()
        return user

    def _update_user_detail(self, user: CustomUser, validated_data: dict) -> UserDetail:
        """유저 상세 정보를 업데이트"""
        user_detail = UserDetail.objects.get(user=user)

        if coffee_life := validated_data.pop("coffee_life", None):
            validated_data["coffee_life"] = {choice: value for choice, value in coffee_life.items() if value is not None}

        if preferred_bean_taste := validated_data.pop("preferred_bean_taste", None):
            validated_data["preferred_bean_taste"] = {choice: value for choice, value in preferred_bean_taste.items() if value is not None}

        for field, value in validated_data.items():
            setattr(user_detail, field, value)

        user_detail.save()
        return user_detail


class CoffeeLifeCategoryService:
    default_categories = UserDetail.COFFEE_LIFE_CHOICES  # 커피 생활 카테고리 종류

    def check_true_categories_by_user(self, user) -> bool:
        user_detail = get_object_or_404(UserDetail, user=user)

        for category in self.default_categories:
            if user_detail.coffee_life[category]:
                return True

        return False

    def get_random_category(self) -> str:
        return random.choice(self.default_categories)

    def get_random_true_category_by_user(self, user) -> str:
        user_detail = get_object_or_404(UserDetail, user=user)
        true_categories = [c for c in self.default_categories if user_detail.coffee_life[c]]

        return random.choice(true_categories)
