import random
from datetime import timedelta
from itertools import chain

from django.db.models import (
    BooleanField,
    Count,
    Exists,
    Prefetch,
    Q,
    Value,
)
from django.shortcuts import get_object_or_404
from django.utils import timezone

from repo.common.view_counter import get_not_viewed_contents
from repo.interactions.like.services import LikeService
from repo.interactions.note.services import NoteService
from repo.interactions.relationship.services import RelationshipService
from repo.records.models import Photo, Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer


def get_relationship_service():
    return RelationshipService()


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
            serializer_data = TastedRecordListSerializer(item, context={"request": request}).data
            obj_list.append(serializer_data)
            # obj_list.append(serialize_tasted_record_list(item, request))
        else:
            serializer_data = PostListSerializer(item, context={"request": request}).data
            obj_list.append(serializer_data)
            # obj_list.append(serialize_post_list(item, request))
    return obj_list


def get_post_feed_queryset(user, add_filter=None, exclude_filter=None, subject=None):  # TODO: post service로 이동 V
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
    like_service = LikeService("post")
    note_service = NoteService()

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
            is_user_liked=Exists(like_service.get_like_subquery_for_post(user)),
            is_user_noted=Exists(note_service.get_note_subquery_for_post(user)),
        )
    )


def get_tasted_record_feed_queryset(user, add_filter=None, exclude_filter=None):  # TODO: tasted record service로 이동
    """
    시음기록 피드를 위한 필터링된 쿼리셋을 생성합니다.

    Args:
        user: 사용자 객체
        add_filter: 추가할 필터 조건 (dict)
        exclude_filter: 제외할 필터 조건 (dict)

    Returns:
        QuerySet: 필터링된 시음기록 쿼리셋
    """
    like_service = LikeService("tasted_record")
    note_service = NoteService()

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
            is_user_liked=Exists(like_service.get_like_subquery_for_tasted_record(user)),
            is_user_noted=Exists(note_service.get_note_subquery_for_tasted_record(user)),
        )
    )


################################ 피드 관련 매서드 ################################
################################ 피드 관련 매서드 ################################
################################ 피드 관련 매서드 ################################


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
    relationship_service = get_relationship_service()
    following_users = relationship_service.get_following_user_list(user.id)
    one_hour_ago = timezone.now() - timedelta(hours=1)

    # 1. 팔로우한 유저의 시음기록, 게시글
    tr_add_filter = {"author__in": following_users, "is_private": False, "created_at__gte": one_hour_ago}
    following_tasted_records = get_tasted_record_feed_queryset(user, tr_add_filter, None)
    following_tasted_records_order = following_tasted_records.order_by("-id")

    p_add_filter = {"author__in": following_users, "created_at__gte": one_hour_ago}
    following_posts = get_post_feed_queryset(user, p_add_filter, None, None)
    following_posts_order = following_posts.order_by("-id")

    # 2. 조회하지 않은 시음기록, 게시글
    not_viewed_tasted_records = get_not_viewed_contents(request, following_tasted_records_order, "tasted_record_viewed")
    not_viewed_posts = get_not_viewed_contents(request, following_posts_order, "post_viewed")

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
    relationship_service = get_relationship_service()
    following_users = relationship_service.get_following_user_list(user.id)
    block_users = relationship_service.get_unique_blocked_user_list(user.id)

    add_filter = {"is_private": False}
    exclude_filter = {"author__in": list(chain(following_users, block_users))}

    # 1. 팔로우하지 않고 차단하지 않은 유저들의 시음기록, 게시글
    common_tasted_records = get_tasted_record_feed_queryset(user, add_filter, exclude_filter)
    common_tasted_records_order = common_tasted_records.order_by("-id")

    common_posts = get_post_feed_queryset(user, None, exclude_filter, None)
    common_posts_order = common_posts.order_by("-id")

    # 2. 조회하지 않은 시음기록, 게시글
    not_viewd_tasted_records = get_not_viewed_contents(request, common_tasted_records_order, "tasted_record_viewed")
    not_viewd_posts = get_not_viewed_contents(request, common_posts_order, "post_viewed")

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
    relationship_service = get_relationship_service()
    block_users = relationship_service.get_unique_blocked_user_list(user.id)

    private_filter = {"is_private": False}
    block_filter = {"author__in": block_users}

    tasted_records = get_tasted_record_feed_queryset(user, add_filter=private_filter, exclude_filter=block_filter)
    tasted_records_order = tasted_records.order_by("?")

    posts = get_post_feed_queryset(user, add_filter=None, exclude_filter=block_filter, subject=None)
    posts_order = posts.order_by("?")

    combined_data = list(chain(tasted_records_order, posts_order))
    random.shuffle(combined_data)

    return combined_data


def get_annonymous_tasted_records_feed():  # TODO: tasted record service로 이동
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


def get_annonymous_posts_feed():  # TODO: post service로 이동
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


################################ 피드 관련 매서드 ################################
################################ 피드 관련 매서드 ################################
################################ 피드 관련 매서드 ################################


# comment, photo에서 사용중
# comment의 서비스에서 model_map 사용하도록 수정
# photo는 utils에서 사용하도록 수정
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
