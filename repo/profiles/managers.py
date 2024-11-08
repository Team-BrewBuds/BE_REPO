import re

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

    def validate_nickname(self, nickname):
        if not nickname or not nickname.strip():
            raise ValueError("닉네임은 공백일 수 없습니다.")

        if not re.match(r"^[가-힣0-9]{2,12}$", nickname):
            raise ValueError("닉네임은 2 ~ 12자의 한글 또는 숫자만 가능합니다.")

        # 닉네임 중복은 model에서 unique 제약조건 검사
        return nickname

    def set_user(self, user, validated_data):
        if "nickname" in validated_data:
            validated_data["nickname"] = self.validate_nickname(validated_data["nickname"])

        for field in validated_data:
            setattr(user, field, validated_data[field])
        user.save()
        return user


class UserDetailManager(models.Manager):

    def get_user_detail(self, user):
        return self.get(user=user)

    def set_user_detail(self, user, validated_data):
        user_detail = self.get_user_detail(user)
        for field in validated_data:
            setattr(user_detail, field, validated_data[field])

        user_detail.save()
        return user_detail


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
        unique_block_users.remove(user_id)

        return unique_block_users
