from django.contrib.auth.models import BaseUserManager
from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404


class CustomUserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_user_and_user_detail(self, id):
        return get_object_or_404(self.select_related("user_detail"), id=id)


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
        following_users = self.filter(from_user=user_id, relationship_type="follow").values_list("to_user", flat=True)
        return following_users

    def blocking(self, user_id):  # 차단한 사용자
        return self.filter(from_user=user_id, relationship_type="block")

    def blocked(self, user_id):  # 나를 차단한 사용자
        return self.filter(to_user=user_id, relationship_type="block")

    def get_unique_blocked_users(self, user_id):
        """내가 차단하거나 나를 차단한 사용자 리스트 조회"""
        block_relationships = self.filter(Q(from_user=user_id) | Q(to_user=user_id), relationship_type="block").values_list(
            "from_user", "to_user"
        )
        block_users = [to_user if from_user == user_id else from_user for from_user, to_user in block_relationships]
        unique_block_users = set(block_users)
        return unique_block_users
