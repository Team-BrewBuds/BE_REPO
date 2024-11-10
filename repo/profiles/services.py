from django.db import models
from django.db.models import Count, Exists, F, Value

from .models import CustomUser, Relationship


def base_user_profile_query(id):
    follower_cnt = Relationship.objects.followers(id).count()
    following_cnt = Relationship.objects.following(id).count()

    return CustomUser.objects.select_related("user_detail").annotate(
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
