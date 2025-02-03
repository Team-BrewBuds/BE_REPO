from django.db.models import Min, OuterRef, Q, Subquery

from repo.common.utils import make_date_format
from repo.interactions.note.models import Note
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


def get_users_activity_report() -> list[dict]:
    """
    사용자 활동 보고서를 생성하는 함수
    """
    users = CustomUser.objects.annotate(
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
        "first_tr_at",
        "first_post_at",
        "second_tr_at",
        "second_post_at",
        "first_noted_tr_at",
        "first_noted_post_at",
        "first_noted_bean_at",
    )

    reports = []

    for user in users:
        reports.append(
            {
                "ID": user["id"],
                "닉네임": user["nickname"],
                "가입일": make_date_format(user["created_at"]) if user["created_at"] else None,
                "첫 시음기록 작성일": (make_date_format(user["first_tr_at"]) if user["first_tr_at"] else None),
                "두번째 시음기록 작성일": (make_date_format(user["second_tr_at"]) if user["second_tr_at"] else None),
                "첫 게시물 작성일": make_date_format(user["first_post_at"]) if user["first_post_at"] else None,
                "두번째 게시물 작성일": (make_date_format(user["second_post_at"]) if user["second_post_at"] else None),
                "첫 시음기록 저장일": (make_date_format(user["first_noted_tr_at"]) if user["first_noted_tr_at"] else None),
                "첫 게시물 저장일": make_date_format(user["first_noted_post_at"]) if user["first_noted_post_at"] else None,
                "첫 원두 정보 저장일": make_date_format(user["first_noted_bean_at"]) if user["first_noted_bean_at"] else None,
            }
        )

    return reports


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
