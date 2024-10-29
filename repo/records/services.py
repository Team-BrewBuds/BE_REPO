import random
from datetime import timedelta
from itertools import chain

from django.db.models import (
    Avg,
    Count,
    Exists,
    FloatField,
    OuterRef,
    Prefetch,
    Q,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone

from repo.beans.models import Bean
from repo.common.view_counter import is_viewed
from repo.profiles.models import Relationship
from repo.records.models import Comment, Photo, Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer


def serialize_tasted_record_list(item, request):
    """TastedRecord 객체를 시리얼라이즈하는 함수"""
    return TastedRecordListSerializer(item, context={"request": request}).data


def serialize_post_list(item, request):
    """Post 객체를 시리얼라이즈하는 함수"""
    return PostListSerializer(item, context={"request": request}).data


def get_serialized_data(request, page_obj_list):
    """
    페이지 객체를 받아 시리얼라이즈된 데이터를 반환하는 함수
    게시글 리스트 or 시음기록 리스트
    """
    obj_list = []
    for item in page_obj_list:
        if isinstance(item, TastedRecord):
            obj_list.append(serialize_tasted_record_list(item, request))
        else:
            obj_list.append(serialize_post_list(item, request))
    return obj_list


def get_following_users(user):
    """사용자가 팔로우한 유저 리스트를 가져오는 함수"""
    return Relationship.objects.following(user.id).values_list("to_user", flat=True)


def get_not_viewed_data(request, queryset, cookie_name):
    """조회하지 않은 데이터를 가져오는 함수"""
    return [data for data in queryset if not is_viewed(request, cookie_name=cookie_name, content_id=data.id)]


def get_user_liked_post_queryset(user):
    return Post.like_cnt.through.objects.filter(post_id=OuterRef("pk"), customuser_id=user.id)


def get_user_noted_post_queryset(user):
    return user.note_set.filter(post_id=OuterRef("pk"), author_id=user.id)


def get_user_liked_tasted_record_queryset(user):
    return TastedRecord.like_cnt.through.objects.filter(tastedrecord_id=OuterRef("pk"), customuser_id=user.id)


def get_user_noted_tasted_record_queryset(user):
    return user.note_set.filter(tasted_record_id=OuterRef("pk"), author_id=user.id)


def get_post_feed_queryset(user, add_filter=None, exclude_filter=None, subject=None):
    """필터링된 Post 쿼리셋을 생성하는 헬퍼 함수"""
    is_user_liked_post_subquery = get_user_liked_post_queryset(user)
    is_user_noted_post_subquery = get_user_noted_post_queryset(user)

    add_filters = Q(**add_filter) if add_filter else Q()
    add_filters &= Q(subject=subject) if subject is not None else Q()

    exclude_filters = Q(**exclude_filter) if exclude_filter else Q()

    return (
        Post.objects.filter(add_filters)
        .exclude(exclude_filters)
        .select_related("author")
        .prefetch_related("tasted_records", "comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
            is_user_liked=Exists(is_user_liked_post_subquery),
            is_user_noted=Exists(is_user_noted_post_subquery),
        )
        .order_by("-id")
    )


def get_tasted_record_feed_queryset(user, add_filter=None, exclude_filter=None):
    """필터링된 TastedRecord 쿼리셋을 생성하는 헬퍼 함수"""
    is_user_liked_tasted_record_subquery = get_user_liked_tasted_record_queryset(user)
    is_user_noted_tasted_record_subquery = get_user_noted_tasted_record_queryset(user)

    add_filters = Q(**add_filter) if add_filter else Q()
    exclude_filters = Q(**exclude_filter) if exclude_filter else Q()

    return (
        TastedRecord.objects.filter(add_filters)
        .exclude(exclude_filters)
        .select_related("author", "bean", "taste_review")
        .prefetch_related("comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
            is_user_liked=Exists(is_user_liked_tasted_record_subquery),
            is_user_noted=Exists(is_user_noted_tasted_record_subquery),
        )
        .order_by("-id")
    )


def get_following_feed(request, user):
    """
    사용자가 팔로잉한 유저들의 1시간 이내 작성한 시음기록과 게시글을 랜덤순으로 가져오는 함수
    30분이내 조회한 기록, 프라이빗한 시음기록은 제외
    """
    following_users = get_following_users(user)
    one_hour_ago = timezone.now() - timedelta(hours=1)

    # 1. 팔로우한 유저의 시음기록, 게시글
    tr_add_filter = {"author__in": following_users, "is_private": False, "created_at__gte": one_hour_ago}
    following_tasted_records = get_tasted_record_feed_queryset(user, tr_add_filter, None)

    p_add_filter = {"author__in": following_users, "created_at__gte": one_hour_ago}
    following_posts = get_post_feed_queryset(user, p_add_filter, None, None)

    # 2. 조회하지 않은 시음기록, 게시글
    not_viewed_tasted_records = get_not_viewed_data(request, following_tasted_records, "tasted_record_viewed")
    not_viewed_posts = get_not_viewed_data(request, following_posts, "post_viewed")

    # 3. 1 + 2
    combined_data = list(chain(not_viewed_tasted_records, not_viewed_posts))

    # 4. 랜덤순으로 섞기
    random.shuffle(combined_data)

    return combined_data


def get_common_feed(request, user):
    """
    일반 시음기록과 게시글을 최신순으로 가져오는 함수
    30분이내 조회한 기록, 프라이빗한 시음기록은 제외
    팔로잉한 유저 기록 제외
    """
    following_users = get_following_users(user)

    add_filter = {"is_private": False}
    exclude_filter = {"author__in": following_users}

    # 1. 팔로우하지 않은 유저들의 시음기록, 게시글
    common_tasted_records = get_tasted_record_feed_queryset(user, add_filter, exclude_filter)
    common_posts = get_post_feed_queryset(user, None, exclude_filter, None)

    # 2. 조회하지 않은 시음기록, 게시글
    not_viewd_tasted_records = get_not_viewed_data(request, common_tasted_records, "tasted_record_viewed")
    not_viewd_posts = get_not_viewed_data(request, common_posts, "post_viewed")

    # 3. 1 + 2 (최신순 done)
    combined_data = list(chain(not_viewd_tasted_records, not_viewd_posts))

    return combined_data


def get_refresh_feed(user):
    """
    시음기록과 게시글을 랜덤순으로 가져오는 함수
    프라이빗한 시음기록은 제외
    """

    is_user_liked_tasted_record_subquery = get_user_liked_tasted_record_queryset(user)
    is_user_noted_tasted_record_subquery = get_user_noted_tasted_record_queryset(user)

    tasted_records = (
        TastedRecord.objects.filter(is_private=False)
        .select_related("author", "bean", "taste_review")
        .prefetch_related("comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
            is_user_liked=Exists(is_user_liked_tasted_record_subquery),
            is_user_noted=Exists(is_user_noted_tasted_record_subquery),
        )
        .order_by("?")
    )

    is_user_liked_post_subquery = get_user_liked_post_queryset(user)
    is_user_noted_post_subquery = get_user_noted_post_queryset(user)

    posts = (
        Post.objects.select_related("author")
        .prefetch_related("tasted_records", "comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
            is_user_liked=Exists(is_user_liked_post_subquery),
            is_user_noted=Exists(is_user_noted_post_subquery),
        )
        .order_by("?")
    )

    combined_data = list(chain(tasted_records, posts))
    random.shuffle(combined_data)

    return combined_data


def get_tasted_record_feed(request, user):
    following_users = get_following_users(user)

    following_users_filter = {"author__in": following_users}
    private_false_filter = {"is_private": False}
    mixin_filter = {**following_users_filter, **private_false_filter}

    # 1. 팔로우한 유저의 시음기록
    followed_tasted_records = get_tasted_record_feed_queryset(user, mixin_filter, None)

    # 2. 팔로우하지 않은 유저의 시음기록
    not_followed_tasted_records = get_tasted_record_feed_queryset(user, private_false_filter, following_users_filter)

    # 3. 1 + 2 (최신순 done)
    tasted_records = list(chain(followed_tasted_records, not_followed_tasted_records))

    # 4. 조회하지 않은 시음기록
    not_viewd_tasted_records = get_not_viewed_data(request, tasted_records, "tasted_record_viewed")

    return not_viewd_tasted_records


def get_tasted_record_detail(pk):
    record = (
        TastedRecord.objects.select_related("author", "bean", "taste_review")
        .prefetch_related(
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
        )
        .get(pk=pk)
    )

    return record


def get_post_feed(request, user, subject):
    """사용자가 팔로우한 유저와 추가 게시글을 가져오는 함수"""
    following_users = get_following_users(user)

    # 1. 팔로우한 유저의 게시글
    following_users_filter = {"author__in": following_users}
    followed_posts = get_post_feed_queryset(user, following_users_filter, None, subject)

    # 2. 팔로우하지 않은 유저의 게시글
    not_followed_posts = get_post_feed_queryset(user, None, following_users_filter, subject)

    # 3.  1 + 2 (최신순 done)
    posts = list(chain(followed_posts, not_followed_posts))

    # 4. 조회하지 않은 게시글
    not_viewed_posts = get_not_viewed_data(request, posts, "post_viewed")

    return not_viewed_posts


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


def get_user_saved_beans(user):
    """사용자가 저장한 원두 리스트와 관련된 bean 및 평균 평점을 가져오는 함수 (찜한 원두 리스트 정보)"""

    saved_beans = (
        Bean.objects.filter(note__author=user)  # 사용자가 저장한 원두
        .prefetch_related("tastedrecord_set__taste_review")  # tasted_record 관련된 taste_review
        .annotate(
            avg_star=Coalesce(  # 평균 평점 계산, null일 경우 0으로 설정
                Avg("tastedrecord__taste_review__star"), 0, output_field=FloatField()
            ),
            tasted_records_cnt=Count("tastedrecord"),  # 시음기록 개수 계산
        )
    )
    return saved_beans
