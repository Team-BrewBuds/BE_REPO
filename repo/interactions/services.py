from django.db import models, transaction
from django.db.models import Exists, Q

from repo.common.exception.exceptions import BadRequestException
from repo.interactions.models import Relationship


class RelationshipService:
    def __init__(self, relationship_repo=Relationship.objects):
        self.relationship_repo = relationship_repo

    def check_relationship(self, from_user, to_user, relationship_type):
        return self.relationship_repo.filter(from_user=from_user, to_user=to_user, relationship_type=relationship_type).exists()

    def double_check_relationships(self, from_user, to_user, relationship_type):
        return self.relationship_repo.filter(
            Q(from_user=from_user, to_user=to_user, relationship_type=relationship_type)
            | Q(from_user=to_user, to_user=from_user, relationship_type=relationship_type)
        ).exists()

    def follow(self, from_user, to_user):
        if self.double_check_relationships(from_user, to_user, "block"):
            return None, False

        relationship, created = self.relationship_repo.get_or_create(from_user=from_user, to_user=to_user, relationship_type="follow")
        return relationship, created

    def unfollow(self, from_user, to_user):
        relationship = self.relationship_repo.filter(from_user=from_user, to_user=to_user, relationship_type="follow")
        if relationship.exists():
            relationship.delete()
            return True
        return False

    @transaction.atomic
    def block(self, from_user, to_user):
        self.unfollow(from_user, to_user)

        relationship, created = self.relationship_repo.get_or_create(from_user=from_user, to_user=to_user, relationship_type="block")
        return relationship, created

    @transaction.atomic
    def unblock(self, from_user, to_user):
        relationship = self.relationship_repo.filter(from_user=from_user, to_user=to_user, relationship_type="block")
        if relationship.exists():
            relationship.delete()
            return True
        return False

    def get_following(self, user_id):
        return self.relationship_repo.filter(from_user=user_id, relationship_type="follow")

    def get_followers(self, user_id):
        return self.relationship_repo.filter(to_user=user_id, relationship_type="follow")

    def get_following_users(self, user_id):
        return self.relationship_repo.filter(from_user=user_id, relationship_type="follow").values_list("to_user", flat=True)

    def get_followers_users(self, user_id):
        return self.relationship_repo.filter(to_user=user_id, relationship_type="follow").values_list("from_user", flat=True)

    def get_blocking(self, user_id):
        return self.relationship_repo.filter(from_user=user_id, relationship_type="block")

    def get_blocked(self, user_id):
        return self.relationship_repo.filter(to_user=user_id, relationship_type="block")

    def get_unique_blocked_users(self, user_id):
        block_relationships = self.relationship_repo.filter(Q(from_user=user_id) | Q(to_user=user_id), relationship_type="block")
        blocking_users = list(block_relationships.values_list("to_user", flat=True))
        blocked_users = list(block_relationships.values_list("from_user", flat=True))
        unique_block_users = list(set(blocking_users + blocked_users))

        if user_id in unique_block_users:
            unique_block_users.remove(user_id)

        return unique_block_users

    def get_user_relationships_by_follow_type(self, follow_type, request_user, target_user=None):
        if target_user is None:
            target_user = request_user

        if follow_type == "following":
            return (
                self.relationship_repo.filter(from_user=target_user.id, relationship_type="follow")
                .select_related("to_user")
                .annotate(
                    is_following=Exists(
                        self.relationship_repo.filter(
                            from_user=models.OuterRef("to_user_id"), to_user=request_user.id, relationship_type="follow"
                        )
                    )
                )
                .order_by("-id")
            )

        elif follow_type == "follower":
            return (
                self.relationship_repo.filter(to_user=target_user.id, relationship_type="follow")
                .select_related("from_user")
                .annotate(
                    is_following=Exists(
                        self.relationship_repo.filter(
                            from_user=request_user, to_user_id=models.OuterRef("from_user_id"), relationship_type="follow"
                        )
                    )
                )
                .order_by("-id")
            )

        else:
            raise BadRequestException("Invalid follow type")
