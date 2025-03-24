from django.db.models import Count, Min, OuterRef, Q, Subquery

from repo.common.utils import make_date_format
from repo.interactions.note.models import Note
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


def get_users_activity_report() -> list[dict]:
    """
    사용자 활동 보고서를 생성하는 함수
    """
    user_activities = CustomUser.objects.annotate(
        tr_count=Count("tastedrecord", distinct=True),
        post_count=Count("post", distinct=True),
        noted_bean_count=Count("note__bean", distinct=True),
        noted_tr_count=Count("note__tasted_record", distinct=True),
        noted_post_count=Count("note__post", distinct=True),
        first_tr_at=Min("tastedrecord__created_at"),
        first_post_at=Min("post__created_at"),
        second_tr_at=get_second_record_subquery(TastedRecord),
        second_post_at=get_second_record_subquery(Post),
        first_noted_tr_at=get_first_note_subquery(Note, "tasted_record"),
        first_noted_post_at=get_first_note_subquery(Note, "post"),
        first_noted_bean_at=get_first_note_subquery(Note, "bean"),
    ).values(
        "id",
        "nickname",
        "created_at",
        "tr_count",
        "post_count",
        "noted_bean_count",
        "noted_tr_count",
        "noted_post_count",
        "first_tr_at",
        "first_post_at",
        "second_tr_at",
        "second_post_at",
        "first_noted_tr_at",
        "first_noted_post_at",
        "first_noted_bean_at",
    )

    return [
        {
            "ID": user_activity["id"],
            "닉네임": user_activity["nickname"],
            "가입일": make_date_format(user_activity["created_at"]),
            "시음기록 작성 개수": user_activity["tr_count"],
            "게시물 작성 개수": user_activity["post_count"],
            "원두정보 저장 개수": user_activity["noted_bean_count"],
            "시음기록 저장 개수": user_activity["noted_tr_count"],
            "게시물 저장 개수": user_activity["noted_post_count"],
            "첫 시음기록 작성일": make_date_format(user_activity["first_tr_at"]),
            "두번째 시음기록 작성일": make_date_format(user_activity["second_tr_at"]),
            "첫 게시물 작성일": make_date_format(user_activity["first_post_at"]),
            "두번째 게시물 작성일": make_date_format(user_activity["second_post_at"]),
            "첫 시음기록 저장일": make_date_format(user_activity["first_noted_tr_at"]),
            "첫 게시물 저장일": make_date_format(user_activity["first_noted_post_at"]),
            "첫 원두 정보 저장일": make_date_format(user_activity["first_noted_bean_at"]),
        }
        for user_activity in user_activities
    ]


def get_second_record_subquery(model: Post | TastedRecord) -> Subquery:
    """
    사용자의 두번째 시음기록 or 게시물 작성일을 조회하는 서브쿼리
    """
    filters = Q(author=OuterRef("id"))
    return Subquery(model.objects.filter(filters).order_by("created_at").values("created_at")[1:2])


def get_first_note_subquery(model: Note, noted_model: str) -> Subquery:
    """
    사용자의 첫번째 저장 시음기록 or 게시물 or 원두 작성일을 조회하는 서브쿼리
    """
    filters = Q(author=OuterRef("id")) & Q(**{f"{noted_model}__isnull": False})
    return Subquery(model.objects.filter(filters).order_by("created_at").values("created_at")[0:1])
