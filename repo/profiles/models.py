from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from repo.profiles.managers import CustomUserManager


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
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name="성별")
    birth = models.IntegerField(null=True, blank=True, verbose_name="출생 연도")
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="이메일")
    login_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        choices=login_type_choices,
        verbose_name="로그인 유형",
    )
    profile_image = models.ImageField(upload_to="profiles/", null=True, blank=True)

    social_id = models.BigIntegerField(null=True, unique=True, blank=False)

    is_staff = models.BooleanField(default=False, verbose_name="관리자 여부")
    is_superuser = models.BooleanField(default=False, verbose_name="슈퍼 관리자 여부")
    is_active = models.BooleanField(default=True, verbose_name="활성 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="가입 일시")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # TODO: 현재 카카오에서 이메일을 받고있는 형태가 아니라서 manager 사용 보류
    objects = CustomUserManager()

    def natural_key(self):
        return (self.email,)

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nickname}"

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"


class UserDetail(models.Model):

    COFFEE_LIFE_CHOICES = ["cafe_tour", "coffee_extraction", "coffee_study", "cafe_alba", "cafe_work", "cafe_operation"]
    TASTE_CHOICES = ["body", "acidity", "bitterness", "sweetness"]

    def default_coffee_life():
        return dict.fromkeys(UserDetail.COFFEE_LIFE_CHOICES, False)

    def default_taste():
        return dict.fromkeys(UserDetail.TASTE_CHOICES, 3)

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="user_detail", verbose_name="사용자")
    introduction = models.TextField(null=True, blank=True, verbose_name="소개글")
    profile_link = models.URLField(max_length=200, null=True, blank=True, verbose_name="프로필 링크")
    coffee_life = models.JSONField(default=default_coffee_life, verbose_name="커피 생활")
    preferred_bean_taste = models.JSONField(default=default_coffee_life, verbose_name="선호하는 원두 맛")
    is_certificated = models.BooleanField(default=False, verbose_name="자격증 여부")

    def __str__(self):
        return f"{self.user.nickname}의 상세정보"

    class Meta:
        db_table = "user_detail"
        verbose_name = "사용자 상세 정보"
        verbose_name_plural = "사용자 상세 정보"
