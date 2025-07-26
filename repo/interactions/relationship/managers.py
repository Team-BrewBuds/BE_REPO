from typing import TYPE_CHECKING, List

from django.db import models
from django.db.models import Case, IntegerField, OuterRef, Q, When

from repo.profiles.models import CustomUser

from .enums import RelationshipType

if TYPE_CHECKING:
    pass


class RelationshipQuerySet(models.QuerySet):
    """
    Relationship 모델의 쿼리셋
    - 재사용 가능한 쿼리셋 메서드를 정의
    """

    def get_relationship_from(self, from_user: CustomUser, relationship_type: str) -> models.QuerySet:
        """특정 유저로부터 관계를 맺은 유저를 필터링"""
        return self.filter(from_user=from_user, relationship_type=relationship_type)

    def get_relationship_to(self, to_user: CustomUser, relationship_type: str) -> models.QuerySet:
        """특정 유저가 관계가 맺어진 유저를 필터링"""
        return self.filter(to_user=to_user, relationship_type=relationship_type)

    def get_relationship_from_to(self, from_user: CustomUser, to_user: CustomUser | OuterRef, relationship_type: str) -> models.QuerySet:
        """두 유저 간의 관계를 필터링

        Args:
            from_user: 관계를 시작하는 유저
            to_user: 관계 대상 유저 또는 OuterRef (서브쿼리용)
            relationship_type: 관계 유형 ("follow", "block")

        Returns:
            QuerySet: 필터링된 관계 쿼리셋

        Note:
            to_user는 일반적인 조회 시 CustomUser 인스턴스를,
            서브쿼리에서 외부 참조 시 OuterRef 인스턴스를 받을 수 있음
        """
        return self.filter(from_user=from_user, to_user=to_user, relationship_type=relationship_type)


class RelationshipManager(models.Manager):
    def get_queryset(self) -> "RelationshipQuerySet":
        return RelationshipQuerySet(self.model, using=self._db)

    def one_way_check(self, from_user: CustomUser, to_user: CustomUser, relationship_type: str) -> bool:
        """
        한 방향으로만 관계를 확인하는 메서드

        Args:
            from_user: 관계를 맺는 유저
            to_user: 관계 대상 유저
            relationship_type: 관계 유형 ("follow", "block")

        """
        return self.get_queryset().get_relationship_from_to(from_user, to_user, relationship_type).exists()

    def two_way_check(self, from_user: CustomUser, to_user: CustomUser, relationship_type: str, operator: str = "or") -> bool:
        """
        두 유저 간의 양방향 관계를 확인하는 범용 메서드

        Args:
            from_user: 관계를 맺는 유저
            to_user: 관계 대상 유저
            relationship_type: 관계 유형 ("follow", "block")
            operator: 논리 연산자 ("or" 또는 "and")

        Returns:
            bool: 조건에 맞는 관계 존재 여부
        """
        condition1 = Q(from_user=from_user, to_user=to_user, relationship_type=relationship_type)
        condition2 = Q(from_user=to_user, to_user=from_user, relationship_type=relationship_type)

        if operator == "and":
            return self.filter(condition1).exists() and self.filter(condition2).exists()
        else:
            return self.filter(condition1 | condition2).exists()

    def get_following(self, user: CustomUser) -> models.QuerySet:
        """
        특정 유저가 팔로우한 유저 목록을 조회하는 메서드
        """
        return self.get_queryset().get_relationship_from(from_user=user, relationship_type=RelationshipType.FOLLOW.name)

    def get_followers(self, user: CustomUser) -> models.QuerySet:
        """
        특정 유저를 팔로우한 유저 목록을 조회하는 메서드
        """
        return self.get_queryset().get_relationship_to(to_user=user, relationship_type=RelationshipType.FOLLOW.name)

    def get_blocking(self, user: CustomUser) -> models.QuerySet:
        """
        특정 유저가 차단한 유저 목록을 조회하는 메서드
        """
        return self.get_queryset().get_relationship_from(from_user=user, relationship_type=RelationshipType.BLOCK.name)

    def get_blocked(self, user: CustomUser) -> models.QuerySet:
        """
        특정 유저가 차단당한 유저 목록을 조회하는 메서드
        """
        return self.get_queryset().get_relationship_to(to_user=user, relationship_type=RelationshipType.BLOCK.name)

    def get_unique_blocked_user_list(self, user: CustomUser) -> List[int]:
        """
        특정 유저와 차단 관계에 있는 유저 목록을 조회하는 메서드
        """

        return (
            self.get_queryset()
            .filter(Q(from_user=user) | Q(to_user=user), relationship_type=RelationshipType.BLOCK.name)
            .annotate(
                other_user_id=Case(
                    When(from_user=user, then="to_user_id"), When(to_user=user, then="from_user_id"), output_field=IntegerField()
                )
            )
            .values_list("other_user_id", flat=True)
            .distinct()
        )

    def get_following_subquery_for_record(self, user: CustomUser) -> models.QuerySet:
        """
        특정 유저가 해당 게시물의 작성자를 팔로우하는지 여부를 조회하는 서브쿼리
        """
        return self.get_queryset().get_relationship_from_to(user, OuterRef("author_id"), RelationshipType.FOLLOW.name)

    def get_blocking_subquery_for_record(self, user: CustomUser) -> models.QuerySet:
        """
        특정 유저가 해당 게시물의 작성자를 차단하는지 여부를 조회하는 서브쿼리
        """
        return self.get_queryset().get_relationship_from_to(user, OuterRef("author_id"), RelationshipType.BLOCK.name)
