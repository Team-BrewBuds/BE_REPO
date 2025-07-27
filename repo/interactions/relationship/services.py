from django.db import models, transaction
from django.db.models import Exists

from repo.common.exception.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from repo.profiles.models import CustomUser

from .enums import RelationshipType
from .models import Relationship


class RelationshipService:
    """관계 관련 비즈니스 로직을 처리하는 서비스"""

    def follow(self, from_user: CustomUser, to_user: CustomUser) -> Relationship:
        """팔로우 관계 생성"""
        if Relationship.objects.one_way_check(from_user, to_user, RelationshipType.FOLLOW.name):
            raise ConflictException("user is already following")

        if Relationship.objects.two_way_check(from_user, to_user, RelationshipType.BLOCK.name, operator="or"):
            raise ForbiddenException("user is blocking or blocked")

        return Relationship.objects.create(from_user=from_user, to_user=to_user, relationship_type=RelationshipType.FOLLOW.name)

    def unfollow(self, from_user: CustomUser, to_user: CustomUser) -> None:
        """팔로우 관계 삭제"""
        if not Relationship.objects.one_way_check(from_user, to_user, RelationshipType.FOLLOW.name):
            raise NotFoundException("user is not following")

        relationship = Relationship.objects.filter(from_user=from_user, to_user=to_user, relationship_type=RelationshipType.FOLLOW.name)
        relationship.delete()

    @transaction.atomic
    def block(self, from_user: CustomUser, to_user: CustomUser) -> Relationship:
        """차단 관계 생성"""
        if from_user == to_user:
            raise BadRequestException("user cannot block itself")

        if Relationship.objects.one_way_check(from_user, to_user, RelationshipType.BLOCK.name):
            raise ConflictException("user is already blocking")

        if Relationship.objects.one_way_check(from_user, to_user, RelationshipType.FOLLOW.name):
            self.unfollow(from_user, to_user)

        return Relationship.objects.create(from_user=from_user, to_user=to_user, relationship_type=RelationshipType.BLOCK.name)

    @transaction.atomic
    def unblock(self, from_user: CustomUser, to_user: CustomUser) -> None:
        """차단 관계 삭제"""
        if not Relationship.objects.one_way_check(from_user, to_user, RelationshipType.BLOCK.name):
            raise NotFoundException("user is not blocking")

        relationship = Relationship.objects.filter(from_user=from_user, to_user=to_user, relationship_type=RelationshipType.BLOCK.name)
        relationship.delete()

    def get_following(self, user: CustomUser) -> models.QuerySet:
        """특정 유저가 팔로잉하는 유저 필터링"""
        return Relationship.objects.get_following(user)

    def get_followers(self, user: CustomUser) -> models.QuerySet:
        """특정 유저를 팔로잉하는 유저 필터링"""
        return Relationship.objects.get_followers(user)

    def get_following_user_list(self, user: CustomUser) -> list[int]:
        """특정 유저가 팔로잉하는 유저 필터링"""
        return self.get_following(user).values_list("to_user", flat=True)

    def get_followers_user_list(self, user: CustomUser) -> list[int]:
        """특정 유저를 팔로잉하는 유저 필터링"""
        return self.get_followers(user).values_list("from_user", flat=True)

    def get_blocking(self, user: CustomUser) -> models.QuerySet:
        """특정 유저가 차단한 유저 필터링"""
        return Relationship.objects.get_blocking(user)

    def get_blocked(self, user: CustomUser) -> models.QuerySet:
        """특정 유저가 차단당한 유저 필터링"""
        return Relationship.objects.get_blocked(user)

    def get_unique_blocked_user_list(self, user: CustomUser) -> list[int]:
        """특정 유저와 차단 관계에 있는 유저 목록을 조회"""
        return Relationship.objects.get_unique_blocked_user_list(user)

    def get_user_relationships_by_follow_type(
        self, follow_type: str, request_user: CustomUser, target_user: CustomUser | None = None
    ) -> list[dict]:
        """특정 유저의 팔로잉 또는 팔로워 관계 조회"""
        if target_user is None:
            target_user = request_user

        base_query = {
            "following": {
                "base": self.get_following(target_user),
                "select_related_field": "to_user",
                "user_field": "to_user",
                "is_following_from_user": request_user,
                "is_following_to_user": models.OuterRef("to_user_id"),
            },
            "follower": {
                "base": self.get_followers(target_user),
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
                        relationship_type=RelationshipType.FOLLOW.name,
                    )
                )
            )
            .order_by("-id")
        )

        return [
            {"user": getattr(relationship, query_config["user_field"]), "is_following": relationship.is_following}
            for relationship in relationships
        ]

    def get_following_subquery_for_record(self, user: CustomUser) -> models.QuerySet:
        """특정 유저가 팔로잉하는 유저 서브쿼리"""
        return Relationship.objects.get_following_subquery_for_record(user)
