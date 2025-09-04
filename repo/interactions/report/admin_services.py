from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery

from repo.common.utils import make_date_format
from repo.interactions.note.models import Note
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


def get_users_activity_report() -> list[dict]:
    """
    사용자 활동 보고서를 생성하는 함수
    """
    user_activities = CustomUser.objects.annotate(
        coffee_life=F("user_detail__coffee_life"),
        is_certificated=F("user_detail__is_certificated"),
        tr_count=get_record_cnt_subquery(TastedRecord),
        post_count=get_record_cnt_subquery(Post),
        noted_bean_count=get_record_cnt_subquery(Note, "bean"),
        noted_tr_count=get_record_cnt_subquery(Note, "tasted_record"),
        noted_post_count=get_record_cnt_subquery(Note, "post"),
        first_tr_at=get_created_at_record_by_seq_subquery(TastedRecord, 1),
        first_post_at=get_created_at_record_by_seq_subquery(Post, 1),
        second_tr_at=get_created_at_record_by_seq_subquery(TastedRecord, 2),
        second_post_at=get_created_at_record_by_seq_subquery(Post, 2),
        first_noted_tr_at=get_created_at_record_by_seq_subquery(Note, 1, "tasted_record"),
        first_noted_post_at=get_created_at_record_by_seq_subquery(Note, 1, "post"),
        first_noted_bean_at=get_created_at_record_by_seq_subquery(Note, 1, "bean"),
    ).values(
        "id",
        "nickname",
        "created_at",
        "gender",
        "birth",
        "coffee_life",
        "is_certificated",
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

    reports = []
    for user_activity in user_activities:
        coffee_life = dict(user_activity["coffee_life"] or {})

        report = {
            "ID": user_activity["id"],
            "닉네임": user_activity["nickname"],
            "가입일": make_date_format(user_activity["created_at"]),
            "성별": user_activity["gender"],
            "출생 연도": user_activity["birth"],
            "카페 알바": coffee_life.get("cafe_alba", False),
            "카페 근무": coffee_life.get("cafe_work", False),
            "카페 운영": coffee_life.get("cafe_operation", False),
            "커피 추출": coffee_life.get("coffee_extraction", False),
            "커피 공부": coffee_life.get("coffee_study", False),
            "카페 투어": coffee_life.get("cafe_tour", False),
            "자격증 여부": user_activity["is_certificated"],
            "시음기록 작성 개수": user_activity["tr_count"] or 0,
            "게시물 작성 개수": user_activity["post_count"] or 0,
            "원두정보 저장 개수": user_activity["noted_bean_count"] or 0,
            "시음기록 저장 개수": user_activity["noted_tr_count"] or 0,
            "게시물 저장 개수": user_activity["noted_post_count"] or 0,
            "첫 시음기록 작성일": make_date_format(user_activity["first_tr_at"]),
            "두번째 시음기록 작성일": make_date_format(user_activity["second_tr_at"]),
            "첫 게시물 작성일": make_date_format(user_activity["first_post_at"]),
            "두번째 게시물 작성일": make_date_format(user_activity["second_post_at"]),
            "첫 시음기록 저장일": make_date_format(user_activity["first_noted_tr_at"]),
            "첫 게시물 저장일": make_date_format(user_activity["first_noted_post_at"]),
            "첫 원두 정보 저장일": make_date_format(user_activity["first_noted_bean_at"]),
        }
        reports.append(report)

    return reports


def get_record_cnt_subquery(model: Post | TastedRecord | Note, noted_model: str | None = None) -> Subquery:
    """
    사용자의 시음기록 or 게시물 or 노트 작성 개수를 조회하는 서브쿼리
    """

    filters = Q(author=OuterRef("id"))
    if noted_model:
        filters &= Q(**{f"{noted_model}__isnull": False})
    return Subquery(model.objects.filter(filters).values("author").annotate(count=Count("id")).values("count"), output_field=IntegerField())


def get_created_at_record_by_seq_subquery(model: Post | TastedRecord | Note, seq: int = 1, noted_model: str | None = None) -> Subquery:
    """
    사용자의 시음기록 or 게시물 or 노트 작성 순서에 따른 작성일을 조회하는 서브쿼리
    """

    filters = Q(author=OuterRef("id"))
    if noted_model:
        filters &= Q(**{f"{noted_model}__isnull": False})
    return Subquery(model.objects.filter(filters).order_by("created_at").values("created_at")[seq - 1 : seq])
