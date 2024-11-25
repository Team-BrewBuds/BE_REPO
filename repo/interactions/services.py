from django.db import models, transaction
from django.db.models import Exists, Q

from repo.common.exception.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from repo.interactions.models import Relationship

FOLLOW_TYPE = "follow"
BLOCK_TYPE = "block"


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
        if self.double_check_relationships(from_user, to_user, BLOCK_TYPE):
            raise ForbiddenException("user is blocking or blocked")

        relationship, created = self.relationship_repo.get_or_create(from_user=from_user, to_user=to_user, relationship_type=FOLLOW_TYPE)

        if not created:
            raise ConflictException("user is already following")

    def unfollow(self, from_user, to_user):
        if not self.check_relationship(from_user, to_user, FOLLOW_TYPE):
            raise NotFoundException("user is not following")

        relationship = self.relationship_repo.filter(from_user=from_user, to_user=to_user, relationship_type=FOLLOW_TYPE)
        relationship.delete()

    @transaction.atomic
    def block(self, from_user, to_user):
        try:
            self.unfollow(from_user, to_user)
        except NotFoundException:
            pass

        relationship, created = self.relationship_repo.get_or_create(from_user=from_user, to_user=to_user, relationship_type=BLOCK_TYPE)

        if not created:
            raise ConflictException("user is already blocking")

    @transaction.atomic
    def unblock(self, from_user, to_user):
        if not self.check_relationship(from_user, to_user, BLOCK_TYPE):
            raise NotFoundException("user is not blocking")

        relationship = self.relationship_repo.filter(from_user=from_user, to_user=to_user, relationship_type=BLOCK_TYPE)
        relationship.delete()

    def get_following(self, user_id):
        return self.relationship_repo.filter(from_user=user_id, relationship_type=FOLLOW_TYPE)

    def get_followers(self, user_id):
        return self.relationship_repo.filter(to_user=user_id, relationship_type=FOLLOW_TYPE)

    def get_following_user_list(self, user_id):
        return self.relationship_repo.get_following(user_id).values_list("to_user", flat=True)

    def get_followers_user_list(self, user_id):
        return self.relationship_repo.get_followers(user_id).values_list("from_user", flat=True)

    def get_blocking(self, user_id):
        return self.relationship_repo.filter(from_user=user_id, relationship_type=BLOCK_TYPE)

    def get_blocked(self, user_id):
        return self.relationship_repo.filter(to_user=user_id, relationship_type=BLOCK_TYPE)

    def get_unique_blocked_user_list(self, user_id):
        block_relationships = self.relationship_repo.filter(Q(from_user=user_id) | Q(to_user=user_id), relationship_type=BLOCK_TYPE)
        blocking_users = list(block_relationships.values_list("to_user", flat=True))
        blocked_users = list(block_relationships.values_list("from_user", flat=True))
        unique_block_users = list(set(blocking_users + blocked_users))

        if user_id in unique_block_users:
            unique_block_users.remove(user_id)

        return unique_block_users

    def get_user_relationships_by_follow_type(self, follow_type, request_user, target_user=None):
        if target_user is None:
            target_user = request_user

        base_query = {
            "following": {
                "base": self.get_following(target_user.id),
                "select_related_field": "to_user",
                "user_field": "to_user",
                "is_following_from_user": models.OuterRef("to_user_id"),
                "is_following_to_user": request_user,
            },
            "follower": {
                "base": self.get_followers(target_user.id),
                "select_related_field": "from_user",
                "user_field": "from_user",
                "is_following_from_user": request_user,
                "is_following_to_user": models.OuterRef("from_user_id"),
            },
        }

        if follow_type not in base_query:
            raise BadRequestException("Invalid follow type")

        query_config = base_query[follow_type]

        relationships = (
            query_config["base"]
            .select_related(query_config["select_related_field"])
            .annotate(
                is_following=Exists(
                    self.relationship_repo.filter(
                        from_user=query_config["is_following_from_user"],
                        to_user_id=query_config["is_following_to_user"],
                        relationship_type=FOLLOW_TYPE,
                    )
                )
            )
            .order_by("-id")
        )

        return [
            {"user": getattr(relationship, query_config["user_field"]), "is_following": relationship.is_following}
            for relationship in relationships
        ]
