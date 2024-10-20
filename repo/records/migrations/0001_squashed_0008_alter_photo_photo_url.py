# Generated by Django 5.1.2 on 2024-10-20 14:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("records", "0001_initial"),
        ("records", "0002_alter_post_subject"),
        ("records", "0003_remove_post_tasted_record_post_tasted_records"),
        ("records", "0004_alter_tastedrecord_like_cnt"),
        ("records", "0005_alter_post_tasted_records"),
        ("records", "0006_alter_post_tasted_records"),
        ("records", "0003_alter_photo_photo_url"),
        ("records", "0007_merge_20241018_2357"),
        ("records", "0008_alter_photo_photo_url"),
    ]

    initial = True

    dependencies = [
        ("beans", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TastedRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField(verbose_name="노트 내용")),
                ("view_cnt", models.IntegerField(default=0, verbose_name="조회수")),
                ("is_private", models.BooleanField(default=False, verbose_name="비공개 여부")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="작성일")),
                ("tag", models.TextField(blank=True, null=True, verbose_name="태그")),
                (
                    "author",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="작성자"),
                ),
                ("bean", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="beans.bean", verbose_name="원두")),
                ("like_cnt", models.ManyToManyField(default=0, related_name="like_tasted_records", to=settings.AUTH_USER_MODEL)),
                (
                    "taste_review",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="beans.beantastereview", verbose_name="맛&평가"),
                ),
            ],
            options={
                "verbose_name": "시음 기록",
                "verbose_name_plural": "시음 기록",
                "db_table": "tasted_record",
            },
        ),
        migrations.CreateModel(
            name="Post",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="제목")),
                ("content", models.TextField(verbose_name="내용")),
                (
                    "subject",
                    models.CharField(
                        choices=[
                            ("전체", "all"),
                            ("일반", "normal"),
                            ("카페", "cafe"),
                            ("원두", "bean"),
                            ("정보", "info"),
                            ("장비", "gear"),
                            ("질문", "question"),
                            ("고민", "worry"),
                        ],
                        max_length=100,
                        verbose_name="주제",
                    ),
                ),
                ("view_cnt", models.IntegerField(default=0, verbose_name="조회수")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="작성일")),
                ("tag", models.TextField(blank=True, null=True, verbose_name="태그")),
                (
                    "author",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="작성자"),
                ),
                ("like_cnt", models.ManyToManyField(related_name="like_posts", to=settings.AUTH_USER_MODEL)),
                (
                    "tasted_records",
                    models.ManyToManyField(blank=True, related_name="posts", to="records.tastedrecord", verbose_name="관련 시음 기록"),
                ),
            ],
            options={
                "verbose_name": "게시글",
                "verbose_name_plural": "게시글",
                "db_table": "post",
            },
        ),
        migrations.CreateModel(
            name="Note",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="작성일")),
                (
                    "author",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="작성자"),
                ),
                (
                    "bean",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="beans.bean", verbose_name="원두"
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="records.post", verbose_name="게시글"
                    ),
                ),
                (
                    "tasted_record",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="records.tastedrecord",
                        verbose_name="시음 기록",
                    ),
                ),
            ],
            options={
                "verbose_name": "노트",
                "verbose_name_plural": "노트",
                "db_table": "note",
            },
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField(verbose_name="내용")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="삭제 여부")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="작성일")),
                (
                    "author",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name="작성자"),
                ),
                ("like_cnt", models.ManyToManyField(related_name="like_comments", to=settings.AUTH_USER_MODEL)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="replies",
                        to="records.comment",
                        verbose_name="상위 댓글",
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="records.post", verbose_name="게시글"
                    ),
                ),
                (
                    "tasted_record",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="records.tastedrecord",
                        verbose_name="시음 기록",
                    ),
                ),
            ],
            options={
                "verbose_name": "댓글",
                "verbose_name_plural": "댓글",
                "db_table": "comment",
            },
        ),
        migrations.CreateModel(
            name="Photo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("photo_url", models.ImageField(blank=True, null=True, upload_to="records/", verbose_name="사진")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="업로드 일자")),
                (
                    "post",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="records.post", verbose_name="관련 게시글"
                    ),
                ),
                (
                    "tasted_record",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="records.tastedrecord",
                        verbose_name="관련 시음 기록",
                    ),
                ),
            ],
            options={
                "verbose_name": "사진",
                "verbose_name_plural": "사진",
                "db_table": "photo",
            },
        ),
    ]