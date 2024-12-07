import random
from datetime import timedelta
from itertools import chain

from django.db.models import (
    Avg,
    BooleanField,
    Count,
    Exists,
    FloatField,
    OuterRef,
    Prefetch,
    Q,
    Value,
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
    """
    시음기록 객체를 시리얼라이즈하여 JSON 형태로 반환합니다.

    Args:
        item: TastedRecord 객체
        request: HTTP 요청 객체

    Returns:
        dict: 시리얼라이즈된 시음기록 데이터
    """
    return TastedRecordListSerializer(item, context={"request": request}).data


def serialize_post_list(item, request):
    """
    게시글 객체를 시리얼라이즈하여 JSON 형태로 반환합니다.

    Args:
        item: Post 객체
        request: HTTP 요청 객체

    Returns:
        dict: 시리얼라이즈된 게시글 데이터
    """
    return PostListSerializer(item, context={"request": request}).data


def get_serialized_data(request, page_obj_list):
    """
    페이지네이션된 객체 리스트를 시리얼라이즈하여 반환합니다.
    게시글과 시음기록 객체를 모두 처리할 수 있습니다.

    Args:
        request: HTTP 요청 객체
        page_obj_list: 페이지네이션된 객체 리스트

    Returns:
        list: 시리얼라이즈된 객체 리스트
    """
    obj_list = []
    for item in page_obj_list:
        if isinstance(item, TastedRecord):
            obj_list.append(serialize_tasted_record_list(item, request))
        else:
            obj_list.append(serialize_post_list(item, request))
    return obj_list


def get_not_viewed_data(request, queryset, cookie_name):
    """
    사용자가 아직 조회하지 않은 데이터만 필터링하여 반환합니다.

    Args:
        request: HTTP 요청 객체
        queryset: 필터링할 쿼리셋
        cookie_name: 조회 여부를 확인할 쿠키 이름

    Returns:
        list: 조회하지 않은 데이터 리스트
    """
    return [data for data in queryset if not is_viewed(request, cookie_name=cookie_name, content_id=data.id)]


def get_user_liked_post_queryset(user):
    """
    사용자가 좋아요한 게시글을 확인하기 위한 서브쿼리를 반환합니다.

    Args:
        user: 사용자 객체

    Returns:
        QuerySet: 좋아요 관계를 확인하는 서브쿼리
    """
    return Post.like_cnt.through.objects.filter(post_id=OuterRef("pk"), customuser_id=user.id)


def get_user_noted_post_queryset(user):
    """
    사용자가 저장한 게시글을 확인하기 위한 서브쿼리를 반환합니다.

    Args:
        user: 사용자 객체

    Returns:
        QuerySet: 저장 관계를 확인하는 서브쿼리
    """
    return user.note_set.filter(post_id=OuterRef("pk"), author_id=user.id)


def get_user_liked_tasted_record_queryset(user):
    """
    사용자가 좋아요한 시음기록을 확인하기 위한 서브쿼리를 반환합니다.

    Args:
        user: 사용자 객체

    Returns:
        QuerySet: 좋아요 관계를 확인하는 서브쿼리
    """
    return TastedRecord.like_cnt.through.objects.filter(tastedrecord_id=OuterRef("pk"), customuser_id=user.id)


def get_user_noted_tasted_record_queryset(user):
    """
    사용자가 저장한 시음기록을 확인하기 위한 서브쿼리를 반환합니다.

    Args:
        user: 사용자 객체

    Returns:
        QuerySet: 저장 관계를 확인하는 서브쿼리
    """
    return user.note_set.filter(tasted_record_id=OuterRef("pk"), author_id=user.id)


def get_post_feed_queryset(user, add_filter=None, exclude_filter=None, subject=None):
    """
    게시글 피드를 위한 필터링된 쿼리셋을 생성합니다.

    Args:
        user: 사용자 객체
        add_filter: 추가할 필터 조건 (dict)
        exclude_filter: 제외할 필터 조건 (dict)
        subject: 게시글 주제

    Returns:
        QuerySet: 필터링된 게시글 쿼리셋
    """
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
    )


def get_tasted_record_feed_queryset(user, add_filter=None, exclude_filter=None):
    """
    시음기록 피드를 위한 필터링된 쿼리셋을 생성합니다.

    Args:
        user: 사용자 객체
        add_filter: 추가할 필터 조건 (dict)
        exclude_filter: 제외할 필터 조건 (dict)

    Returns:
        QuerySet: 필터링된 시음기록 쿼리셋
    """
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
    )


def get_following_feed(request, user):
    """
    팔로잉 중인 사용자들의 최근 활동 피드를 반환합니다.

    - 1시간 이내 작성된 시음기록과 게시글을 포함
    - 비공개 시음기록과 최근 조회한 기록은 제외
    - 결과는 랜덤 순서로 정렬됨

    Args:
        request: HTTP 요청 객체
        user: 사용자 객체

    Returns:
        list: 시음기록과 게시글이 혼합된 피드 리스트
    """
    following_users = Relationship.objects.get_following_users(user.id)
    one_hour_ago = timezone.now() - timedelta(hours=1)

    # 1. 팔로우한 유저의 시음기록, 게시글
    tr_add_filter = {"author__in": following_users, "is_private": False, "created_at__gte": one_hour_ago}
    following_tasted_records = get_tasted_record_feed_queryset(user, tr_add_filter, None)
    following_tasted_records_order = following_tasted_records.order_by("-id")

    p_add_filter = {"author__in": following_users, "created_at__gte": one_hour_ago}
    following_posts = get_post_feed_queryset(user, p_add_filter, None, None)
    following_posts_order = following_posts.order_by("-id")

    # 2. 조회하지 않은 시음기록, 게시글
    not_viewed_tasted_records = get_not_viewed_data(request, following_tasted_records_order, "tasted_record_viewed")
    not_viewed_posts = get_not_viewed_data(request, following_posts_order, "post_viewed")

    # 3. 1 + 2
    combined_data = list(chain(not_viewed_tasted_records, not_viewed_posts))

    # 4. 랜덤순으로 섞기
    random.shuffle(combined_data)

    return combined_data


def get_common_feed(request, user):
    """
    일반 피드를 반환합니다.

    - 팔로잉하지 않은 사용자들의 공개 시음기록과 게시글 포함
    - 차단한 사용자의 컨텐츠 제외
    - 최근 조회한 기록 제외
    - 최신순으로 정렬

    Args:
        request: HTTP 요청 객체
        user: 사용자 객체

    Returns:
        list: 시음기록과 게시글이 최신순으로 정렬된 피드 리스트
    """
    following_users = Relationship.objects.get_following_users(user.id)
    block_users = Relationship.objects.get_unique_blocked_users(user.id)

    add_filter = {"is_private": False}
    exclude_filter = {"author__in": list(chain(following_users, block_users))}

    # 1. 팔로우하지 않고 차단하지 않은 유저들의 시음기록, 게시글
    common_tasted_records = get_tasted_record_feed_queryset(user, add_filter, exclude_filter)
    common_tasted_records_order = common_tasted_records.order_by("-id")

    common_posts = get_post_feed_queryset(user, None, exclude_filter, None)
    common_posts_order = common_posts.order_by("-id")

    # 2. 조회하지 않은 시음기록, 게시글
    not_viewd_tasted_records = get_not_viewed_data(request, common_tasted_records_order, "tasted_record_viewed")
    not_viewd_posts = get_not_viewed_data(request, common_posts_order, "post_viewed")

    # 3. 1 + 2 (최신순 done)
    combined_data = sorted(chain(not_viewd_tasted_records, not_viewd_posts), key=lambda x: x.created_at, reverse=True)
    return combined_data


def get_refresh_feed(user):
    """
    새로고침용 랜덤 피드를 반환합니다.

    - 모든 공개 시음기록과 게시글 포함
    - 차단한 사용자의 컨텐츠 제외
    - 랜덤 순서로 정렬

    Args:
        user: 사용자 객체

    Returns:
        list: 시음기록과 게시글이 랜덤으로 정렬된 피드 리스트
    """
    block_users = Relationship.objects.get_unique_blocked_users(user.id)
    private_filter = {"is_private": False}
    block_filter = {"author__in": block_users}

    tasted_records = get_tasted_record_feed_queryset(user, add_filter=private_filter, exclude_filter=block_filter)
    tasted_records_order = tasted_records.order_by("?")

    posts = get_post_feed_queryset(user, add_filter=None, exclude_filter=block_filter, subject=None)
    posts_order = posts.order_by("?")

    combined_data = list(chain(tasted_records_order, posts_order))
    random.shuffle(combined_data)

    return combined_data


def get_annonymous_tasted_records_feed():
    """
    비로그인 사용자를 위한 시음기록 피드를 반환합니다.

    - 공개된 시음기록만 포함
    - 좋아요와 저장 상태는 항상 False
    - 랜덤 순서로 정렬

    Returns:
        QuerySet: 랜덤으로 정렬된 시음기록 쿼리셋
    """
    return (
        TastedRecord.objects.filter(is_private=False)
        .select_related("author", "bean", "taste_review")
        .prefetch_related("comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
            is_user_liked=Value(False, output_field=BooleanField()),
            is_user_noted=Value(False, output_field=BooleanField()),
        )
        .order_by("?")
    )


def get_annonymous_posts_feed():
    """
    비로그인 사용자를 위한 게시글 피드를 반환합니다.

    - 모든 게시글 포함
    - 좋아요와 저장 상태는 항상 False
    - 랜덤 순서로 정렬

    Returns:
        QuerySet: 랜덤으로 정렬된 게시글 쿼리셋
    """
    return (
        Post.objects.select_related("author")
        .prefetch_related("tasted_records", "comment_set", "note_set", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .annotate(
            likes=Count("like_cnt", distinct=True),
            comments=Count("comment", distinct=True),
            is_user_liked=Value(False, output_field=BooleanField()),
            is_user_noted=Value(False, output_field=BooleanField()),
        )
        .order_by("?")
    )


def annonymous_user_feed():
    """
    비로그인 사용자를 위한 통합 피드를 반환합니다.

    - 공개 시음기록과 모든 게시글 포함
    - 랜덤 순서로 정렬

    Returns:
        list: 시음기록과 게시글이 랜덤으로 정렬된 피드 리스트
    """
    tasted_records = get_annonymous_tasted_records_feed()
    posts = get_annonymous_posts_feed()

    combined_data = list(chain(tasted_records, posts))
    random.shuffle(combined_data)

    return combined_data


def get_tasted_record_feed(request, user):
    """
    시음기록 전용 피드를 반환합니다.

    - 팔로잉한 사용자의 모든 시음기록과 다른 사용자의 공개 시음기록 포함
    - 차단한 사용자의 시음기록 제외
    - 최근 조회한 기록 제외
    - 최신순으로 정렬

    Args:
        request: HTTP 요청 객체
        user: 사용자 객체

    Returns:
        list: 최신순으로 정렬된 시음기록 리스트
    """
    following_users = Relationship.objects.get_following_users(user.id)
    block_users = Relationship.objects.get_unique_blocked_users(user.id)

    following_users_filter = {"author__in": following_users}
    private_false_filter = {"is_private": False}
    mixin_filter = {**following_users_filter, **private_false_filter}

    # 1. 팔로우한 유저의 시음기록
    followed_tasted_records = get_tasted_record_feed_queryset(user, add_filter=mixin_filter, exclude_filter=None)
    followed_tasted_records_order = followed_tasted_records.order_by("-id")

    # 2. 팔로우하지 않고 차단하지 않은 유저의 시음기록
    following_and_block_users_filter = {"author__in": list(chain(following_users, block_users))}
    not_followed_tasted_records = get_tasted_record_feed_queryset(
        user, add_filter=private_false_filter, exclude_filter=following_and_block_users_filter
    )
    not_followed_tasted_records_order = not_followed_tasted_records.order_by("-id")

    # 3. 1 + 2 (최신순 done)
    tasted_records = list(chain(followed_tasted_records_order, not_followed_tasted_records_order))

    # 4. 조회하지 않은 시음기록
    not_viewd_tasted_records = get_not_viewed_data(request, tasted_records, "tasted_record_viewed")

    return not_viewd_tasted_records


def get_tasted_record_detail(pk):
    """
    시음기록 상세 정보를 반환합니다.

    Args:
        pk: 시음기록 ID

    Returns:
        TastedRecord: 시음기록 객체
    """
    record = (
        TastedRecord.objects.select_related("author", "bean", "taste_review")
        .prefetch_related(
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
        )
        .get(pk=pk)
    )

    return record


def get_post_feed(request, user, subject):
    """
    게시글 전용 피드를 반환합니다.

    - 팔로잉한 사용자의 게시글과 다른 사용자의 게시글 포함
    - 차단한 사용자의 게시글 제외
    - 최근 조회한 기록 제외
    - 주제별 필터링 가능
    - 최신순으로 정렬

    Args:
        request: HTTP 요청 객체
        user: 사용자 객체
        subject: 게시글 주제

    Returns:
        list: 최신순으로 정렬된 게시글 리스트
    """
    following_users = Relationship.objects.get_following_users(user.id)
    block_users = Relationship.objects.get_unique_blocked_users(user.id)

    # 1. 팔로우한 유저의 게시글
    following_users_filter = {"author__in": following_users}
    followed_posts = get_post_feed_queryset(user, add_filter=following_users_filter, exclude_filter=None, subject=subject)
    followed_posts_order = followed_posts.order_by("-id")

    # 2. 팔로우하지 않고 차단하지않은 유저의 게시글
    following_and_block_users_filter = {"author__in": list(chain(following_users, block_users))}
    not_followed_posts = get_post_feed_queryset(user, add_filter=None, exclude_filter=following_and_block_users_filter, subject=subject)
    not_followed_posts_order = not_followed_posts.order_by("-id")

    # 3.  1 + 2 (최신순 done)
    posts = list(chain(followed_posts_order, not_followed_posts_order))

    # 4. 조회하지 않은 게시글
    not_viewed_posts = get_not_viewed_data(request, posts, "post_viewed")

    return not_viewed_posts


def get_post_detail(post_id):
    """
    게시글 상세 정보를 반환합니다.

    Args:
        post_id: 게시글 ID

    Returns:
        Post: 게시글 객체
    """
    post = (
        Post.objects.select_related("author")
        .prefetch_related(
            Prefetch("tasted_records", queryset=TastedRecord.objects.select_related("bean", "taste_review")),
            Prefetch("photo_set", queryset=Photo.objects.only("photo_url")),
        )
        .get(pk=post_id)
    )

    return post


def get_post_or_tasted_record_detail(object_type, object_id):
    """
    게시글 또는 시음기록의 상세 정보를 반환합니다.

    Args:
        object_type: 객체 타입 ('post' 또는 'tasted_record')
        object_id: 객체 ID

    Returns:
        Post or TastedRecord: 요청된 객체

    Raises:
        ValueError: 유효하지 않은 object_type이 전달된 경우
    """
    if object_type == "post":
        obj = get_object_or_404(Post, pk=object_id)
    elif object_type == "tasted_record":
        obj = get_object_or_404(TastedRecord, pk=object_id)
    else:
        raise ValueError("invalid object_type")

    return obj


def get_post_or_tasted_record_or_comment(object_type, object_id):
    """
    게시글, 시음기록 또는 댓글의 상세 정보를 반환합니다.

    Args:
        object_type: 객체 타입 ('post', 'tasted_record' 또는 'comment')
        object_id: 객체 ID

    Returns:
        Post or TastedRecord or Comment: 요청된 객체
    """
    model_map = {"post": Post, "tasted_record": TastedRecord, "comment": Comment}
    model_class = model_map.get(object_type)
    return get_object_or_404(model_class, pk=object_id)


def get_comment_list(object_type, object_id, user):
    """
    게시글 또는 시음기록에 달린 댓글 목록을 반환합니다.

    - 차단한 사용자의 댓글 제외
    - 대댓글 포함
    - 작성 순서대로 정렬

    Args:
        object_type: 객체 타입 ('post' 또는 'tasted_record')
        object_id: 객체 ID
        user: 사용자 객체

    Returns:
        QuerySet: 댓글 목록
    """
    obj = get_post_or_tasted_record_detail(object_type, object_id)
    block_users = Relationship.objects.get_unique_blocked_users(user.id)

    comments = obj.comment_set.filter(parent=None).exclude(author__in=block_users).order_by("id")
    for comment in comments:
        comment.replies_list = comment.replies.exclude(author__in=block_users).order_by("id")

    return comments


def get_comment(comment_id):
    """
    댓글 상세 정보를 반환합니다.

    Args:
        comment_id: 댓글 ID

    Returns:
        Comment: 댓글 객체
    """
    comment = Comment.objects.get(pk=comment_id)
    return comment


def get_user_posts_by_subject(user, subject):
    """
    사용자가 작성한 주제별 게시글 목록을 반환합니다.

    Args:
        user: 사용자 객체
        subject: 게시글 주제 ('all'인 경우 모든 주제)

    Returns:
        QuerySet: 최신순으로 정렬된 게시글 목록
    """
    subject_filter = Q(subject=subject) if subject != "all" else Q()
    posts = (
        user.post_set.filter(subject_filter)
        .select_related("author")
        .prefetch_related("tasted_records", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .order_by("-id")
    )

    return posts


def get_user_tasted_records_by_filter(user):
    """
    사용자가 작성한 시음기록 목록을 반환합니다.

    - 좋아요 수 포함
    - 필요한 필드만 선택적으로 가져옴

    Args:
        user: 사용자 객체

    Returns:
        QuerySet: 시음기록 목록
    """
    queryset = (
        user.tastedrecord_set.select_related("bean", "taste_review")
        .prefetch_related("like_cnt", Prefetch("photo_set", queryset=Photo.objects.only("photo_url")))
        .only("id", "bean__name", "taste_review__star", "created_at", "like_cnt")
        .annotate(
            likes=Count("like_cnt", distinct=True),
        )
    )
    return queryset


def get_user_saved_beans(user):
    """
    사용자가 저장한 원두 목록과 관련 통계를 반환합니다.

    - 평균 평점 계산 (없는 경우 0)
    - 시음기록 수 포함
    - 필요한 필드만 선택적으로 가져옴

    Args:
        user: 사용자 객체

    Returns:
        QuerySet: 저장된 원두 목록과 통계 정보
    """
    saved_beans = (
        Bean.objects.filter(note__author=user)
        .prefetch_related("tastedrecord_set__taste_review")
        .annotate(
            avg_star=Coalesce(Avg("tastedrecord__taste_review__star"), 0, output_field=FloatField()),
            tasted_records_cnt=Count("tastedrecord"),  # 시음기록 개수 계산
        )
        .values("id", "name", "origin_country", "roast_point", "avg_star", "tasted_records_cnt")
    )
    return saved_beans
