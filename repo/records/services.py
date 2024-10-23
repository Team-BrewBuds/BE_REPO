import random
from datetime import timedelta
from itertools import chain

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from repo.common.view_counter import is_viewed
from repo.profiles.models import Relationship
from repo.records.models import Comment, Photo, Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer


def get_serialized_data(request, page_obj):
    """
    페이지 객체를 받아 시리얼라이즈된 데이터를 반환하는 함수
    게시글 리스트 or 시음기록 리스트
    """
    obj_list = []
    for item in page_obj.object_list:
        serializer = TastedRecordListSerializer if isinstance(item, TastedRecord) else PostListSerializer
        obj_list.append(serializer(item, context={"request": request}).data)

    return obj_list


def get_following_feed(request, user):
    """
    사용자가 팔로잉한 유저들의 1시간 이내 작성한 시음기록과 게시글을 랜덤순으로 가져오는 함수
    30분이내 조회한 기록, 프라이빗한 시음기록은 제외
    """
    following_users = Relationship.objects.following(user.id).values_list("to_user", flat=True)
    one_hour_ago = timezone.now() - timedelta(hours=1)

    following_tasted_record = (
        TastedRecord.objects.filter(author__in=following_users, is_private=False, created_at__gte=one_hour_ago)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-id")
    )

    following_post = (
        Post.objects.filter(author__in=following_users, created_at__gte=one_hour_ago)
        .select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-id")
    )

    # 30분 이내 조회한 시음 기록 제외
    not_viewed_tasted_record = [
        record for record in following_tasted_record if not is_viewed(request, cookie_name="tasted_record_viewed", content_id=record.id)
    ]

    # 30분 이내 조회한 게시글 제외
    not_viewed_post = [post for post in following_post if not is_viewed(request, cookie_name="post_viewed", content_id=post.id)]

    # 두 쿼리셋 결합
    combined_data = list(chain(not_viewed_tasted_record, not_viewed_post))
    random.shuffle(combined_data)

    return combined_data


def get_common_feed(request, user):
    """
    일반 시음기록과 게시글을 최신순으로 가져오는 함수
    30분이내 조회한 기록, 프라이빗한 시음기록은 제외
    팔로잉한 유저 기록 제외
    """
    following_users = Relationship.objects.following(user.id).values_list("to_user", flat=True)

    common_tasted_record = (
        TastedRecord.objects.filter(is_private=False)
        .exclude(author__in=following_users)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    common_post = (
        Post.objects.exclude(author__in=following_users)
        .select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    not_viewed_tasted_record = [
        record for record in common_tasted_record if not is_viewed(request, cookie_name="tasted_record_viewed", content_id=record.id)
    ]

    not_viewed_post = [post for post in common_post if not is_viewed(request, cookie_name="post_viewed", content_id=post.id)]

    combined_data = sorted(chain(not_viewed_tasted_record, not_viewed_post), key=lambda x: x.created_at, reverse=True)

    return combined_data


def get_refresh_feed():
    """
    시음기록과 게시글을 랜덤순으로 가져오는 함수
    프라이빗한 시음기록은 제외
    """

    tasted_records = (
        TastedRecord.objects.filter(is_private=False)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("?")
    )

    posts = (
        Post.objects.select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("?")
    )

    combined_data = list(chain(tasted_records, posts))
    random.shuffle(combined_data)

    return combined_data


def get_tasted_record_feed(user):
    following_users = Relationship.objects.following(user.id).values_list("to_user", flat=True)

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

    return all_records


def get_tasted_record_feed2():
    tasted_records = (
        TastedRecord.objects.filter(is_private=False)
        .select_related("author", "bean", "taste_review")
        .prefetch_related(Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    return tasted_records


def get_tasted_record_detail(pk):
    record = (
        TastedRecord.objects.select_related("author", "bean", "taste_review")
        .prefetch_related(
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
        )
        .get(pk=pk)
    )

    return record


def get_post_feed(user, subject):
    """사용자가 팔로우한 유저와 추가 게시글을 가져오는 함수"""

    # 팔로우한 유저들의 ID 가져오기
    following_users = Relationship.objects.following(user.id).values_list("to_user", flat=True)

    # 기본 필터 조건 (subject에 따른 필터 처리)
    post_filter = Q(author__in=following_users)
    if subject != "all":
        post_filter &= Q(subject=subject)

    # 팔로우한 유저들의 게시글 가져오기
    following_posts = (
        Post.objects.filter(post_filter)
        .select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-created_at")
    )

    # 팔로우한 유저가 없거나 게시글이 10개 미만일 경우 추가 게시글 가져오기
    if not following_users.exists() or following_posts.count() < 10:
        additional_filter = ~Q(author__in=following_users)  # 팔로우한 유저 제외
        if subject != "all":
            additional_filter &= Q(subject=subject)

        additional_posts = (
            Post.objects.filter(additional_filter)
            .select_related("author")
            .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
            .order_by("-created_at")
        )
    else:
        additional_posts = []

    posts = list(chain(following_posts, additional_posts))
    return posts


def get_post_detail(post_id):

    post = (
        Post.objects.select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .get(pk=post_id)
    )

    return post


def get_post_or_tasted_record_detail(object_type, object_id):
    if object_type == "post":
        obj = get_object_or_404(Post, pk=object_id)
    elif object_type == "tasted_record":
        obj = get_object_or_404(TastedRecord, pk=object_id)

    return obj


def get_comment_list(object_type, object_id):
    obj = get_post_or_tasted_record_detail(object_type, object_id)

    comments = obj.comment_set.filter(parent=None).order_by("created_at")
    for comment in comments:
        comment.replies_list = comment.replies.all().order_by("created_at")

    return comments


def get_comment(comment_id):
    comment = Comment.objects.get(pk=comment_id)
    return comment


def get_user_posts_by_subject(user, subject):
    """사용자가 작성한 주제별 게시글 리스트를 가져오는 함수"""

    subject_filter = Q(subject=subject) if subject != "all" else Q()
    posts = (
        user.post_set.filter(subject_filter)
        .select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-id")
    )

    return posts


def get_user_tasted_records_by_filter(user):
    """사용자가 작성한 주제별 시음기록 리스트를 가져오는 함수"""

    queryset = user.tastedrecord_set.select_related("author", "bean", "taste_review").prefetch_related(
        Prefetch("photo_set", queryset=Photo.objects.only("photo_url"))
    )
    return queryset
