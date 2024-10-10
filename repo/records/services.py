from datetime import timedelta
from itertools import chain

from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone

from repo.profiles.models import Relationship
from repo.records.models import Comment, Photo, Post, TastedRecord

# TODO
# - user 인자를 받아서 팔로우한 사용자의 시음 기록만 가져오기(추후 이것으로 변경)
# - 차단한 사용자의 시음 기록은 가져오지 않기


def get_following_feed(user, page=1):

    following_users = Relationship.custom_objects.following(user).values_list("to_user", flat=True)
    one_hour_ago = timezone.now() - timedelta(hours=1)

    following_Tasted_Record = (
        TastedRecord.objects.filter(author__in=following_users, is_private=False, created_at__gte=one_hour_ago)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    following_Post = (
        Post.objects.filter(author__in=following_users, created_at__gte=one_hour_ago)
        .select_related("author", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    # 각각 페이징 처리
    paginator_Tasted_Record = Paginator(following_Tasted_Record, 5)
    paginator_Post = Paginator(following_Post, 5)

    # 페이지 가져오기
    page_obj_Tasted_Record = paginator_Tasted_Record.get_page(page)
    page_obj_Post = paginator_Post.get_page(page)

    # 페이지 결합
    all_records = list(chain(page_obj_Tasted_Record.object_list, page_obj_Post.object_list))
    all_records = sorted(all_records, key=lambda x: x.created_at, reverse=True)

    has_next = page_obj_Tasted_Record.has_next() or page_obj_Post.has_next()

    return all_records, has_next


def get_common_feed(user, page=1, last_id=None):

    one_hour_ago = timezone.now() - timedelta(hours=1)

    following_Tasted_Record = (
        TastedRecord.objects.filter(is_private=False, created_at__gte=one_hour_ago, id__gt=last_id)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    following_Post = (
        Post.objects.filter(created_at__gte=one_hour_ago, id__gt=last_id)
        .select_related("author", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    # 각각 페이징 처리
    paginator_Tasted_Record = Paginator(following_Tasted_Record, 5)
    paginator_Post = Paginator(following_Post, 5)

    # 페이지 가져오기
    page_obj_Tasted_Record = paginator_Tasted_Record.get_page(page)
    page_obj_Post = paginator_Post.get_page(page)

    # 페이지 결합
    all_records = list(chain(page_obj_Tasted_Record.object_list, page_obj_Post.object_list))
    all_records = sorted(all_records, key=lambda x: x.created_at, reverse=True)

    has_next = page_obj_Tasted_Record.has_next() or page_obj_Post.has_next()

    return all_records, has_next


def get_tasted_record_feed(user, page=1):
    following_users = user.following.all()

    followed_records = (
        TastedRecord.objects.filter(author__in=following_users, is_private=False)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    if not following_users.exists() or followed_records.count() < 10:
        additional_records = (
            TastedRecord.objects.filter(is_private=False)
            .exclude(author__in=following_users)
            .select_related("author", "bean", "taste_review")
            .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .order_by("-created_at")
        )
    else:
        additional_records = TastedRecord.objects.none()

    all_records = list(chain(followed_records, additional_records))

    paginator = Paginator(all_records, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_tasted_record_feed2(user, page=1):
    records = (
        TastedRecord.objects.filter(is_private=False)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_tasted_record_detail(record_id):
    record = (
        TastedRecord.objects.select_related("author", "bean", "taste_review")
        .prefetch_related(
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
        )
        .get(pk=record_id)
    )

    return record


def get_post_feed(user, page=1):
    following_users = user.following.all()

    followed_posts = (
        Post.objects.filter(author__in=following_users)
        .select_related("author", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    if not following_users.exists() or followed_posts.count() < 10:
        additional_posts = (
            Post.objects.filter(is_private=False)
            .exclude(author__in=following_users)
            .select_related("author", "taste_and_review")
            .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .order_by("-created_at")
        )
    else:
        additional_posts = TastedRecord.objects.none()

    all_posts = list(chain(followed_posts, additional_posts))

    paginator = Paginator(all_posts, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_post_feed2(user, page=1):

    posts = (
        Post.objects.select_related("author", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_post_detail(post_id):

    post = (
        Post.objects.select_related("author", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .get(pk=post_id)
    )

    return post


def get_post_or_tasted_record_detail(object_type, object_id):
    if object_type == "post":
        obj = get_object_or_404(Post, pk=object_id)
    elif object_type == "tasted_record":
        obj = get_object_or_404(TastedRecord, pk=object_id)

    return obj


def get_comment_list(object_type, object_id, page):
    obj = get_post_or_tasted_record_detail(object_type, object_id)

    comments = obj.comment_set.filter(parent=None).order_by("created_at")
    paginator = Paginator(comments, 10)
    page_obj = paginator.get_page(page)

    for comment in page_obj.object_list:
        comment.replies_list = comment.replies.all().order_by("created_at")

    return page_obj.object_list, page_obj.has_next()


def get_comment(comment_id):
    comment = Comment.objects.get(pk=comment_id)
    return comment
