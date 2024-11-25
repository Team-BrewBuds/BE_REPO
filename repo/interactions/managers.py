from django.db import models, transaction
from django.db.models import Q


class RelationshipManager(models.Manager):

    # 일방향 관계 확인
    def check_relationship(self, from_user, to_user, relationship_type):
        return self.filter(from_user=from_user, to_user=to_user, relationship_type=relationship_type).exists()

    # 양방향 관계 확인
    def double_check_relationships(self, from_user, to_user, relationship_type):
        relationship_exists = self.filter(
            Q(from_user=from_user, to_user=to_user, relationship_type=relationship_type)
            | Q(from_user=to_user, to_user=from_user, relationship_type=relationship_type)
        ).exists()

        return relationship_exists

    def follow(self, from_user, to_user):
        # 둘 중 한명이 차단하고 있는 경우 팔로우 불가
        block_exists = self.double_check_relationships(from_user, to_user, "block")
        if block_exists:
            return None, False

        relationship, created = self.get_or_create(from_user=from_user, to_user=to_user, relationship_type="follow")
        return relationship, created

    def unfollow(self, from_user, to_user):
        relationship = self.filter(from_user=from_user, to_user=to_user, relationship_type="follow")
        if relationship.exists():
            relationship.delete()
            return True
        return False

    @transaction.atomic
    def block(self, from_user, to_user):
        _ = self.unfollow(from_user, to_user)

        relationship, created = self.get_or_create(from_user=from_user, to_user=to_user, relationship_type="block")
        return relationship, created

    def unblock(self, from_user, to_user):
        relationship = self.filter(from_user=from_user, to_user=to_user, relationship_type="block")
        if relationship.exists():
            relationship.delete()
            return True
        return False

    def following(self, user_id):  # 팔로우한 사용자
        return self.filter(from_user=user_id, relationship_type="follow")

    def followers(self, user_id):  # 나를 팔로우한 사용자
        return self.filter(to_user=user_id, relationship_type="follow")

    def get_following_users(self, user_id):
        return self.filter(from_user=user_id, relationship_type="follow").values_list("to_user", flat=True)

    def blocking(self, user_id):  # 차단한 사용자
        return self.filter(from_user=user_id, relationship_type="block")

    def blocked(self, user_id):  # 나를 차단한 사용자
        return self.filter(to_user=user_id, relationship_type="block")

    def get_unique_blocked_users(self, user_id):
        """내가 차단하거나 나를 차단한 사용자 리스트 조회"""
        block_relationships = self.filter(Q(from_user=user_id) | Q(to_user=user_id), relationship_type="block")
        blocking_users = list(block_relationships.values_list("to_user", flat=True))
        blocked_users = list(block_relationships.values_list("from_user", flat=True))
        unique_block_users = list(set(blocking_users + blocked_users))

        if user_id in unique_block_users:
            unique_block_users.remove(user_id)

        return unique_block_users
