from django.contrib.auth.models import BaseUserManager
from django.db import models, transaction
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

    def check_relationship(self, from_user, to_user, relationship_type):
        return self.filter(from_user=from_user, to_user=to_user, relationship_type=relationship_type).exists()

    def follow(self, from_user, to_user):
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

    def blocking(self, user_id):  # 차단한 사용자
        return self.filter(from_user=user_id, relationship_type="block")

    def blocked(self, user_id):  # 나를 차단한 사용자
        return self.filter(to_user=user_id, relationship_type="block")
