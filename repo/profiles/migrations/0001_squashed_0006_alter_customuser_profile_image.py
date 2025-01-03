# Generated by Django 5.1.2 on 2024-10-20 14:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import repo.profiles.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("nickname", models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name="닉네임")),
                ("gender", models.CharField(blank=True, max_length=10, null=True)),
                ("birth", models.DateField(blank=True, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                (
                    "login_type",
                    models.CharField(
                        blank=True, choices=[("naver", "네이버"), ("kakao", "카카오"), ("apple", "애플")], max_length=50, null=True
                    ),
                ),
                ("profile_image", models.ImageField(blank=True, null=True, upload_to="profiles/")),
                ("social_id", models.BigIntegerField(null=True, unique=True)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_superuser", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "사용자",
                "verbose_name_plural": "사용자",
                "db_table": "user",
            },
        ),
        migrations.CreateModel(
            name="UserDetail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("introduction", models.TextField(blank=True, null=True, verbose_name="소개")),
                ("profile_link", models.URLField(blank=True, null=True, verbose_name="프로필 링크")),
                ("coffee_life", models.JSONField(default=repo.profiles.models.UserDetail.default_coffee_life, verbose_name="커피 생활")),
                (
                    "preferred_bean_taste",
                    models.JSONField(default=repo.profiles.models.UserDetail.default_taste, verbose_name="선호하는 원두 맛"),
                ),
                ("is_certificated", models.BooleanField(default=False, verbose_name="인증 여부")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="user_detail", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "verbose_name": "사용자 상세 정보",
                "verbose_name_plural": "사용자 상세 정보",
                "db_table": "user_detail",
            },
        ),
        migrations.CreateModel(
            name="Relationship",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "relationship_type",
                    models.CharField(choices=[("follow", "팔로우"), ("block", "차단")], max_length=10, verbose_name="관계 유형"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="생성일")),
                (
                    "from_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="relationships_from", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "to_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="relationships_to", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "verbose_name": "관계",
                "verbose_name_plural": "관계",
                "db_table": "relationship",
            },
        ),
    ]
