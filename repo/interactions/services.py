from django.db import models
from django.db.models import Exists

from repo.interactions.models import Relationship


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
