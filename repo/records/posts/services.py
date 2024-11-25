from datetime import timedelta

from django.db.models import Count, Exists
from django.utils import timezone

from repo.interactions.models import Relationship
from repo.profiles.models import CustomUser
from repo.records.models import Photo, Post, TastedRecord
from repo.records.services import get_user_liked_post_queryset


def set_post_tasted_records(post: Post, tasted_records: list[TastedRecord]):
    """게시글에 시음기록 연결"""
    if tasted_records:
        post.tasted_records.set(tasted_records)


def set_post_photos(post: Post, photos: list[Photo]):
    """게시글에 사진 연결"""
    if photos:
        post.photo_set.set(photos)


def create_post(user: CustomUser, validated_data: dict) -> Post:
    """게시글 생성 및 관련 데이터 설정"""
    post = Post.objects.create(
        author=user,
        title=validated_data["title"],
        content=validated_data["content"],
        subject=validated_data["subject"],
        tag=validated_data.get("tag", None),
    )

    set_post_tasted_records(post, validated_data.get("tasted_records"))
    set_post_photos(post, validated_data.get("photos"))

    return post


def update_post(post: Post, validated_data: dict) -> Post:
    """게시글 수정 및 관련 데이터 업데이트"""
    for attr, value in validated_data.items():
        if attr not in ["tasted_records", "photos"]:
            setattr(post, attr, value)
    post.save()

    set_post_tasted_records(post, validated_data.get("tasted_records"))
    set_post_photos(post, validated_data.get("photos"))

    return post


def get_top_subject_weekly_posts(user, subject):
    """특정 주제의 게시글 중 일주일 안에 조회수 상위 60개를 가져오는 함수"""
    time_threshold = timezone.now() - timedelta(days=7)
    top_posts_base = Post.objects.filter(created_at__gte=time_threshold).annotate(
        likes=Count("like_cnt", distinct=True),
        comments=Count("comment", distinct=True),
    )

    if subject:
        top_posts_base = top_posts_base.filter(subject=subject)
    if user is None:
        return top_posts_base.order_by("-view_cnt")[:60]

    block_users = Relationship.objects.get_unique_blocked_users(user.id)
    top_posts = (
        top_posts_base.exclude(author__in=block_users)
        .annotate(
            is_user_liked=Exists(get_user_liked_post_queryset(user)),
        )
        .order_by("-view_cnt")[:60]
    )

    return top_posts
