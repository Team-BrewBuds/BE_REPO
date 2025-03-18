from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer
from repo.search.serializers import *

Search_Tag = "Search"
Suggest_Tag = "Suggest Query Word"


class SuggestSchema:
    buddy_suggest_schema = extend_schema(
        parameters=[BuddySuggestInputSerializer],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "추천 검색어 목록",
                        }
                    },
                },
                description="검색어 추천 성공",
            ),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="사용자 닉네임 검색어 12개 추천 API",
        description="""
            입력한 검색어와 부분 일치하는 사용자 닉네임 추천 목록을 반환합니다.
            담당자: blakej2432
        """,
        tags=[Suggest_Tag],
    )

    bean_suggest_schema = extend_schema(
        parameters=[BeanSuggestInputSerializer],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "추천 검색어 목록",
                        }
                    },
                },
                description="검색어 추천 성공",
            ),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="공식 원두 검색어 12개 추천 API",
        description="""
            입력한 검색어와 부분 일치하는 원두 이름 추천 목록을 반환합니다.
            담당자: blakej2432
        """,
        tags=[Suggest_Tag],
    )

    tastedrecord_suggest_schema = extend_schema(
        parameters=[TastedRecordSuggestInputSerializer],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "추천 검색어 목록",
                        }
                    },
                },
                description="검색어 추천 성공",
            ),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="시음기록 검색어 12개 추천 API",
        description="""
            입력한 검색어와 부분 일치하는 원두 이름 추천 목록을 반환합니다.
            담당자: blakej2432
        """,
        tags=[Suggest_Tag],
    )

    post_suggest_schema = extend_schema(
        parameters=[PostSuggestInputSerializer],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "추천 검색어 목록",
                        }
                    },
                },
                description="검색어 추천 성공",
            ),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="게시글 검색어 12개 추천 API",
        description="""
            입력한 검색어와 부분 일치하는 게시글 제목 추천 목록을 반환합니다.
            담당자: blakej2432
        """,
        tags=[Suggest_Tag],
    )

    buddy_suggest_schema_view = extend_schema_view(get=buddy_suggest_schema)
    bean_suggest_schema_view = extend_schema_view(get=bean_suggest_schema)
    tastedrecord_suggest_schema_view = extend_schema_view(get=tastedrecord_suggest_schema)
    post_suggest_schema_view = extend_schema_view(get=post_suggest_schema)


class SearchSchema:
    buddy_search_schema = extend_schema(
        parameters=[BuddySearchInputSerializer, PageNumberSerializer],
        responses={
            200: BuddySearchSerializer(many=True),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="사용자 검색 API",
        description="""
            입력한 검색어와 부분 일치하는 사용자 목록을 반환합니다.

            정렬 기준:
            - record_cnt: 기록 수 기준 내림차순 정렬
            - follower_cnt: 팔로워 수 기준 내림차순 정렬

            담당자: blakej2432
        """,
        tags=[Search_Tag],
    )

    bean_search_schema = extend_schema(
        parameters=[BeanSearchInputSerializer, PageNumberSerializer],
        responses={
            200: BeanSearchSerializer(many=True),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="원두 검색 API",
        description="""
            입력한 검색어와 부분 일치하는 공식 원두 목록을 반환합니다.

            정렬 기준:
            - record_count: 기록 수 기준 내림차순 정렬
            - avg_star: 평균 별점 기준 내림차순 정렬

            필터링 옵션:
            - bean_type: 원두 유형
            - origin_country: 원산지
            - min_star: 최소 별점 (0~5)
            - max_star: 최대 별점 (0~5)
            - is_decaf: 디카페인 여부 (true/false)

            담당자: blakej2432
        """,
        tags=[Search_Tag],
    )

    tastedrecord_search_schema = extend_schema(
        parameters=[TastedRecordSearchInputSerializer, PageNumberSerializer],
        responses={
            200: TastedRecordSearchSerializer(many=True),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="시음기록 검색 API",
        description="""
            입력한 검색어와 부분 일치하는 시음기록 목록을 반환합니다.
            검색 대상: 내용, 원두 이름, 태그, 맛 설명

            정렬 기준:
            - star_rank: 별점 기준 내림차순 정렬
            - latest: 최신순 정렬
            - like_rank: 좋아요 수 기준 내림차순 정렬

            필터링 옵션:
            - bean_type: 원두 유형
            - origin_country: 원산지
            - min_star: 최소 별점 (0~5)
            - max_star: 최대 별점 (0~5)
            - is_decaf: 디카페인 여부 (true/false)

            담당자: blakej2432
        """,
        tags=[Search_Tag],
    )

    post_search_schema = extend_schema(
        parameters=[PostSearchInputSerializer, PageNumberSerializer],
        responses={
            200: PostSearchSerializer(many=True),
            400: OpenApiResponse(description="잘못된 요청"),
        },
        summary="게시글 검색 API",
        description="""
            입력한 검색어와 부분 일치하는 게시글 목록을 반환합니다.
            검색 대상: 제목, 내용

            정렬 기준:
            - latest: 최신순 정렬
            - like_rank: 좋아요 수 기준 내림차순 정렬

            필터링 옵션:
            - subject: 게시글 주제

            담당자: blakej2432
        """,
        tags=[Search_Tag],
    )

    buddy_search_schema_view = extend_schema_view(get=buddy_search_schema)
    bean_search_schema_view = extend_schema_view(get=bean_search_schema)
    tastedrecord_search_schema_view = extend_schema_view(get=tastedrecord_search_schema)
    post_search_schema_view = extend_schema_view(get=post_search_schema)
