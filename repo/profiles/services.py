from django.db import models

from .models import CustomUser, Relationship


def get_user_profile(id):
    user_profile = (
        CustomUser.objects.filter(id=id)
        .select_related("user_detail")
        .prefetch_related("post_set", "relationships_to__from_user", "relationships_from__to_user")  # followers  # following
        .annotate(
            coffee_life=models.F("user_detail__coffee_life"),
            follower_cnt=models.Count("relationships_to", filter=models.Q(relationships_to__relationship_type="follow")),
            following_cnt=models.Count("relationships_from", filter=models.Q(relationships_from__relationship_type="follow")),
            post_cnt=models.Count("post"),
        )
        .first()
    )

    return user_profile


def get_following_list(user, is_mine):
    """사용자가 팔로우한 유저 리스트 반환"""
    followings = Relationship.objects.following(user).all()
    # 자신의 팔로잉은 모두 True로 설정
    is_following = True if is_mine else Relationship.objects.check_relationship(user, user, "follow")

    data = [
        {
            "id": u.to_user.id,
            "nickname": u.to_user.nickname,
            "profile_image": u.to_user.profile_image,
            "is_following": is_following,
        }
        for u in followings
    ]
    return data


def get_follower_list(user):
    """사용자를 팔로우한 유저 리스트 반환"""
    followers = Relationship.objects.followers(user).all()
    data = [
        {
            "id": u.from_user.id,
            "nickname": u.from_user.nickname,
            "profile_image": u.from_user.profile_image,
            "is_following": Relationship.objects.check_relationship(user, u.from_user, "follow"),
        }
        for u in followers
    ]
    return data
