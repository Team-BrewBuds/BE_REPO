from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.search.suggest.serializers import *

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
