from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view

from repo.common.serializers import PageNumberSerializer
from repo.records.tasted_record.serializers import (
    TastedRecordCreateUpdateSerializer,
    TastedRecordDetailSerializer,
    TastedRecordListSerializer,
)

TastedRecord_Tag = "TastedRecord"


class TastedRecordSchema:
    tasted_record_list_get_schema = extend_schema(
        parameters=[PageNumberSerializer],
        responses={200: TastedRecordListSerializer},
        summary="홈 [시음기록] 피드 조회",
        description="""
            홈 피드의 시음기록 list를 최신순으로 가져옵니다.
            - 순서: 팔로잉, 일반
            - 정렬: 최신순
            - 페이지네이션 적용 (12개)
            - 30분이내 조회하지않은 게시글 가져옵니다.
            - 프라이빗한 시음기록은 제외

            Notice:
            - like_cnt에서 likes로 변경
            - comments(댓글 수), is_user_noted(사용자 저장여부) 추가 됨
            - 비회원일경우 랜덤으로 시음기록을 가져옵니다.

            담당자: hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_create_post_schema = extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            201: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request (taste_review.star type: float)"),
        },
        summary="시음기록 생성",
        description="""
            단일 시음기록을 생성합니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_list_create_schema_view = extend_schema_view(get=tasted_record_list_get_schema, post=tasted_record_create_post_schema)

    tasted_record_detail_get_schema = extend_schema(
        responses={200: TastedRecordDetailSerializer},
        summary="시음기록 상세 조회",
        description="""
            시음기록의 상세 정보를 가져옵니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_put_schema = extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            200: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
        summary="시음기록 수정",
        description="""
            시음기록의 정보를 수정합니다. (전체 수정)
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_patch_schema = extend_schema(
        request=TastedRecordCreateUpdateSerializer,
        responses={
            200: TastedRecordDetailSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
        summary="시음기록 수정",
        description="""
            시음기록의 정보를 수정합니다. (일부 수정)
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_delete_schema = extend_schema(
        responses={204: OpenApiResponse(description="No Content")},
        summary="시음기록 삭제",
        description="""
            시음기록을 삭제합니다.
            담당자 : hwstar1204
        """,
        tags=[TastedRecord_Tag],
    )

    tasted_record_detail_schema_view = extend_schema_view(
        get=tasted_record_detail_get_schema,
        put=tasted_record_detail_put_schema,
        patch=tasted_record_detail_patch_schema,
        delete=tasted_record_detail_delete_schema,
    )
