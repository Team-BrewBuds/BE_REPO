from itertools import chain

from django.core.paginator import Paginator
from django.db.models import Prefetch

from .models import Photo, Post, Tasted_Record

# TODO
# - user 인자를 받아서 팔로우한 사용자의 시음 기록만 가져오기(추후 이것으로 변경)
# - 차단한 사용자의 시음 기록은 가져오지 않기


def get_tasted_record_feed(user, page=1):
    following_users = user.following.all()

    followed_records = (
        Tasted_Record.objects.filter(user__in=following_users, is_private=False)
        .select_related("user", "bean", "taste_and_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    if not following_users.exists() or followed_records.count() < 10:
        additional_records = (
            Tasted_Record.objects.filter(is_private=False)
            .exclude(user__in=following_users)
            .select_related("user", "bean", "taste_and_review")
            .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .order_by("-created_at")
        )
    else:
        additional_records = Tasted_Record.objects.none()

    all_records = list(chain(followed_records, additional_records))

    paginator = Paginator(all_records, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_tasted_record_feed2(user, page=1):
    records = (
        Tasted_Record.objects.filter(is_private=False)
        .select_related("user", "bean", "taste_and_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_tasted_record_detail(record_id):
    record = (
        Tasted_Record.objects.select_related("user", "bean", "taste_and_review")
        .prefetch_related(
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
        )
        .get(pk=record_id)
    )

    return record


def get_post_feed(user, page=1):
    following_users = user.following.all()

    followed_posts = (
        Post.objects.filter(user__in=following_users)
        .select_related("user", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    if not following_users.exists() or followed_posts.count() < 10:
        additional_posts = (
            Post.objects.filter(is_private=False)
            .exclude(user__in=following_users)
            .select_related("user", "taste_and_review")
            .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .order_by("-created_at")
        )
    else:
        additional_posts = Tasted_Record.objects.none()

    all_posts = list(chain(followed_posts, additional_posts))

    paginator = Paginator(all_posts, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()


def get_post_feed2(user, page=1):

    posts = (
        Post.objects.select_related("user", "tasted_record")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(page)

    return page_obj.object_list, page_obj.has_next()

def get_post_detail(post_id):

    post = (
        Post.objects.select_related("user", "tasted_record")
        .prefetch_related(
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url"))
        )
        .get(pk=post_id)
    )

    print(post)

    return post

