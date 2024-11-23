import random

from django.db import models, transaction
from django.db.models import Count, Exists, F, QuerySet, Value
from rest_framework.generics import get_object_or_404

from .models import CustomUser, Relationship, UserDetail


class UserService:
    def __init__(self, user_repo=CustomUser.objects, user_detail_repo=UserDetail.objects):
        self.user_repo = user_repo
        self.user_detail_repo = user_detail_repo

    def check_user_exists(self, id: int) -> bool:
        """유저 존재 여부 확인"""
        return self.user_repo.filter(id=id).exists()

    def get_user_by_id(self, id: int) -> CustomUser:
        """유저 조회"""
        return get_object_or_404(self.user_repo, id=id)

    def get_user_profile(self, user: CustomUser) -> dict:
        """유저 프로필 조회"""
        queryset = self.get_profile_base_queryset(user.id)
        return queryset.filter(id=user.id).first()

    def get_other_user_profile(self, user_id: int, other_user_id: int) -> dict:
        """다른 유저 프로필 조회"""
        is_user_following = Relationship.objects.check_relationship(user_id, other_user_id, "follow")
        is_user_blocking = Relationship.objects.check_relationship(user_id, other_user_id, "block")

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
        follower_cnt = Relationship.objects.followers(id).count()
        following_cnt = Relationship.objects.following(id).count()

        return self.user_repo.select_related("user_detail").annotate(
            introduction=F("user_detail__introduction"),
            profile_link=F("user_detail__profile_link"),
            coffee_life=F("user_detail__coffee_life"),
            following_cnt=Value(follower_cnt),
            follower_cnt=Value(following_cnt),
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
        user_detail = self.user_detail_repo.get(user=user)
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


def get_following_list(user):
    """사용자가 팔로우한 유저 리스트 반환"""
    followings = (
        Relationship.objects.following(user)
        .select_related("to_user")
        .annotate(
            is_following=Exists(
                Relationship.objects.filter(from_user=user, to_user_id=models.OuterRef("to_user_id"), relationship_type="follow")
            )
        )
    )

    return followings


def get_follower_list(user):
    """사용자를 팔로우한 유저 리스트 반환"""
    followers = (
        Relationship.objects.followers(user)
        .select_related("from_user")
        .annotate(
            is_following=Exists(
                Relationship.objects.filter(from_user=user, to_user_id=models.OuterRef("from_user_id"), relationship_type="follow")
            ),
        )
    )

    return followers


def get_user_relationships_by_follow_type(user, follow_type):
    if follow_type == "following":
        return get_following_list(user).order_by("-id")
    elif follow_type == "follower":
        return get_follower_list(user).order_by("-id")

    return None
