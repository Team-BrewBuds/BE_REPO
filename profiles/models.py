# create user model with additional fields
from django.db import models


class User(models.Model):

    login_type_choices = [
        ("naver", "네이버"),
        ("kakao", "카카오"),
        ("apple", "애플"),
    ]

    user_id = models.AutoField(primary_key=True)
    nickname = models.CharField(max_length=100, null=False, unique=True, verbose_name="닉네임")
    gender = models.BooleanField(null=True, verbose_name="성별")  # 남/여 구분
    birth = models.DateField(null=True, verbose_name="생일")
    email = models.EmailField(null=False, unique=True, verbose_name="이메일")
    login_type = models.CharField(max_length=50, choices=login_type_choices, verbose_name="로그인 방식")
    profile_image = models.URLField(max_length=500, null=True, verbose_name="프로필 이미지 URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="가입일")

    def __str__(self):
        return self.nickname

    class Meta:
        db_table = "user"
        verbose_name = "사용자"
        verbose_name_plural = "사용자"
