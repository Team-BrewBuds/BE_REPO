from django.db import models, transaction
from django.db.models import Case, Exists, OuterRef, Q, When

from repo.common.exception.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)

from .models import Relationship

FOLLOW_TYPE = "follow"
BLOCK_TYPE = "block"


class RelationshipService:
    """관계 관련 비즈니스 로직을 처리하는 서비스"""

    def check_relationship(self, from_user, to_user, relationship_type):
        return Relationship.objects.filter(from_user=from_user, to_user=to_user, relationship_type=relationship_type).exists()

    def double_check_relationships(self, from_user, to_user, relationship_type):
        return Relationship.objects.filter(
            Q(from_user=from_user, to_user=to_user, relationship_type=relationship_type)
            | Q(from_user=to_user, to_user=from_user, relationship_type=relationship_type)
        ).exists()

    def follow(self, from_user, to_user):
        if self.double_check_relationships(from_user, to_user, BLOCK_TYPE):
            raise ForbiddenException("user is blocking or blocked")

        relationship, created = Relationship.objects.get_or_create(from_user=from_user, to_user=to_user, relationship_type=FOLLOW_TYPE)

        if not created:
            raise ConflictException("user is already following")

    def unfollow(self, from_user, to_user):
        if not self.check_relationship(from_user, to_user, FOLLOW_TYPE):
            raise NotFoundException("user is not following")

        relationship = Relationship.objects.filter(from_user=from_user, to_user=to_user, relationship_type=FOLLOW_TYPE)
        relationship.delete()

    @transaction.atomic
    def block(self, from_user, to_user):
        try:
            self.unfollow(from_user, to_user)
        except NotFoundException:
            pass

        relationship, created = Relationship.objects.get_or_create(from_user=from_user, to_user=to_user, relationship_type=BLOCK_TYPE)

        if not created:
            raise ConflictException("user is already blocking")

    @transaction.atomic
    def unblock(self, from_user, to_user):
        if not self.check_relationship(from_user, to_user, BLOCK_TYPE):
            raise NotFoundException("user is not blocking")

        relationship = Relationship.objects.filter(from_user=from_user, to_user=to_user, relationship_type=BLOCK_TYPE)
        relationship.delete()

    def get_following(self, user_id):
        return Relationship.objects.filter(from_user=user_id, relationship_type=FOLLOW_TYPE)

    def get_followers(self, user_id):
        return Relationship.objects.filter(to_user=user_id, relationship_type=FOLLOW_TYPE)

    def get_following_user_list(self, user_id):
        return self.get_following(user_id).values_list("to_user", flat=True)

    def get_followers_user_list(self, user_id):
        return self.get_followers(user_id).values_list("from_user", flat=True)

    def get_blocking(self, user_id):
        return Relationship.objects.filter(from_user=user_id, relationship_type=BLOCK_TYPE)

    def get_blocked(self, user_id):
        return Relationship.objects.filter(to_user=user_id, relationship_type=BLOCK_TYPE)

    def get_unique_blocked_user_list(self, user_id: int):
        """특정 유저와 차단 관계에 있는 유저 목록을 조회하는 메서드"""
        return (
            Relationship.objects.filter(Q(from_user=user_id) | Q(to_user=user_id), relationship_type=BLOCK_TYPE)
            .values("from_user", "to_user")
            .values_list(
                Case(
                    When(from_user=user_id, then="to_user"),
                    When(to_user=user_id, then="from_user"),
                ),
                flat=True,
            )
            .distinct()
        )

    def get_user_relationships_by_follow_type(self, follow_type, request_user, target_user=None):
        if target_user is None:
            target_user = request_user

        base_query = {
            "following": {
                "base": self.get_following(target_user.id),
                "select_related_field": "to_user",
                "user_field": "to_user",
                "is_following_from_user": request_user,
                "is_following_to_user": models.OuterRef("to_user_id"),
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
                    Relationship.objects.filter(
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

    def get_following_subquery_for_record(self, user):
        return Relationship.objects.filter(relationship_type=FOLLOW_TYPE, from_user=user.id, to_user=OuterRef("author_id"))
