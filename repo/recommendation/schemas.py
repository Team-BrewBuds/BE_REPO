from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

Recommend_Tag = "recommend"


class BudyRecommendSchema:
    budy_recommend_get_schema = extend_schema(
        summary="버디 추천",
        description="""
            유저의 커피 즐기는 방식 6개 중 한가지 방식에 해당 하는 유저 리스트 반환 (10명 랜덤순)
            카테고리 리스트: "cafe_tour", "coffee_extraction", "coffee_study", "cafe_alba", "cafe_work", "cafe_operation"
        """,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        "Example Response",
                        value={
                            "users": [
                                {
                                    "user": {"id": 1, "nickname": "sunjayang", "profile_image": "/media/profiles/dummyimage.png"},
                                    "follower_cnt": 10,
                                },
                                {
                                    "user": {"id": 2, "nickname": "rson", "profile_image": "/media/profiles/dummyimage.png"},
                                    "follower_cnt": 10,
                                },
                            ],
                            "category": "cafe_tour",
                        },
                    )
                ],
                description="Success",
            ),
            401: OpenApiResponse(description="user not authenticated"),
            404: OpenApiResponse(description="Not Found"),
        },
        tags=[Recommend_Tag],
    )

    budy_recommend_schema_view = extend_schema_view(get=budy_recommend_get_schema)
