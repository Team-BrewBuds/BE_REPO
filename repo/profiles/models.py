# create user model with additional fields
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from repo.profiles.helpers import CoffeeLifeHelper, PreferredBeanTasteHelper

# from profiles.managers import CustomUserManager
from repo.profiles.managers import RelationshipManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    사용자 커스텀 모델 (CustomUser)

    사용자 정보를 저장하고 관리하는 모델로, 이메일을 기반으로 인증하며,
    소셜 로그인에 필요한 필드와 일반 사용자 관련 필드들을 포함합니다.
    """

    login_type_choices = [
        ("naver", "네이버"),
        ("kakao", "카카오"),
        ("apple", "애플"),
    ]

    nickname = models.CharField(max_length=50, unique=True, null=True, blank=True, verbose_name="닉네임")
    gender = models.CharField(max_length=10, null=True, blank=True)
    birth = models.IntegerField(null=True, blank=True, verbose_name="출생 연도")
    email = models.EmailField(unique=True, null=True, blank=True)
    login_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=login_type_choices,
    )
    profile_image = models.CharField(max_length=255, null=True, blank=True)

    social_id = models.BigIntegerField(null=True, unique=True, blank=False)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # TODO: 현재 카카오에서 이메일을 받고있는 형태가 아니라서 manager 사용 보류
    # objects = CustomUserManager()

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email}"

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"


# class User(models.Model):
#     user_id = models.AutoField(primary_key=True)
#     nickname = models.CharField(max_length=100, null=False, unique=True, verbose_name="닉네임")
#     gender = models.BooleanField(null=True, verbose_name="성별")  # 남/여 구분
#     birth = models.DateField(null=True, verbose_name="생일")
#     email = models.EmailField(null=False, unique=True, verbose_name="이메일")
#     login_type = models.CharField(max_length=50, choices=login_type_choices, verbose_name="로그인 방식")
#     profile_image = models.URLField(max_length=500, null=True, verbose_name="프로필 이미지 URL")
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="가입일")


class UserDetail(models.Model):

    COFFEE_LIFE_CHOICES = ["cafe_tour", "coffee_extraction", "coffee_study", "cafe_alba", "cafe_work", "cafe_operation"]
    TASTE_CHOICES = ["body", "acidity", "bitterness", "sweetness"]
    
    def default_coffee_life():
        return dict.fromkeys(UserDetail.COFFEE_LIFE_CHOICES, False)

    def default_taste():
        return dict.fromkeys(UserDetail.TASTE_CHOICES, 3)

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="user_detail")
    introduction = models.TextField(null=True, blank=True, verbose_name="소개")
    profile_link = models.URLField(max_length=200, null=True, blank=True, verbose_name="프로필 링크")
    coffee_life = models.JSONField(default=default_coffee_life, verbose_name="커피 생활")
    preferred_bean_taste = models.JSONField(default=default_coffee_life, verbose_name="선호하는 원두 맛")
    is_certificated = models.BooleanField(default=False, verbose_name="인증 여부")

    def get_coffee_life_helper(self):
        return CoffeeLifeHelper(self.coffee_life)

    def get_preferred_bean_taste_helper(self):
        return PreferredBeanTasteHelper(self.preferred_bean_taste)

    def __str__(self):
        return f"{self.user.nickname}의 상세정보"

    class Meta:
        db_table = "user_detail"
        verbose_name = "사용자 상세 정보"
        verbose_name_plural = "사용자 상세 정보"


class Relationship(models.Model):

    RELATIONSHIP_TYPE_CHOICES = [
        ("follow", "팔로우"),
        ("block", "차단"),
    ]

    from_user = models.ForeignKey(CustomUser, related_name="relationships_from", on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name="relationships_to", on_delete=models.CASCADE)
    relationship_type = models.CharField(max_length=10, choices=RELATIONSHIP_TYPE_CHOICES, verbose_name="관계 유형")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    custom_objects = RelationshipManager()
    objects = models.Manager()

    def __str__(self):
        return f"{self.from_user.nickname} {self.get_relationship_type_display()} {self.to_user.nickname}"

    class Meta:
        db_table = "relationship"
        verbose_name = "관계"
        verbose_name_plural = "관계"
