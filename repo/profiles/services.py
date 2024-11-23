import random

from django.db import models
from django.db.models import Count, Exists, F, Value
from rest_framework.generics import get_object_or_404

from .models import CustomUser, Relationship, UserDetail


class UserService:
    def __init__(self, user_repository=None):
        self.user_repository = user_repository or CustomUser.objects

    def check_user_exists(self, id: int) -> bool:
        """유저 존재 여부 확인"""
        return self.user_repository.filter(id=id).exists()


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


def base_user_profile_query(id):
    follower_cnt = Relationship.objects.followers(id).count()
    following_cnt = Relationship.objects.following(id).count()

    return CustomUser.objects.select_related("user_detail").annotate(
        introduction=F("user_detail__introduction"),
        profile_link=F("user_detail__profile_link"),
        coffee_life=F("user_detail__coffee_life"),
        following_cnt=Value(follower_cnt),
        follower_cnt=Value(following_cnt),
        post_cnt=Count("post"),
    )


def get_user_profile(id):
    return base_user_profile_query(id).filter(id=id).first()


def get_other_user_profile(request_user_id, other_user_id):
    is_user_following = Relationship.objects.check_relationship(request_user_id, other_user_id, "follow")
    is_user_blocking = Relationship.objects.check_relationship(request_user_id, other_user_id, "block")

    return (
        base_user_profile_query(request_user_id)
        .filter(id=other_user_id)
        .annotate(is_user_following=Value(is_user_following), is_user_blocking=Value(is_user_blocking))
        .first()
    )


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
