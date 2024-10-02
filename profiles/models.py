from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from profiles.managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    사용자 커스텀 모델 (CustomUser)

    사용자 정보를 저장하고 관리하는 모델로, 이메일을 기반으로 인증하며, 
    소셜 로그인에 필요한 필드와 일반 사용자 관련 필드들을 포함합니다.
    """
    nickname = models.CharField(max_length=50, null=True, blank=True, verbose_name='사용자 닉네임')
    gender = models.CharField(max_length=10, null=True, blank=True)
    birth = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    login_type = models.CharField(max_length=50, null=True, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
    
    
    social_id = models.BigIntegerField(
        null=True, unique=True, blank=False
    )  

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
        return self.email