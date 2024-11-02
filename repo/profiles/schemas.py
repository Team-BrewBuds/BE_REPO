from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.beans.serializers import UserBeanSerializer
from repo.common.serializers import PageNumberSerializer
from repo.profiles.serializers import (
    UserBlockListSerializer,
    UserFollowListSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)
from repo.records.models import Post
from repo.records.posts.serializers import UserPostSerializer
from repo.records.serializers import UserNoteSerializer
from repo.records.tasted_record.serializers import UserTastedRecordSerializer

Profile_Tag = "profiles"
Follow_Tag = "follow"
Block_Tag = "block"
Recommend_Tag = "recommend"
Profile_Records_Tag = "profile_records"


class ProfileSchema:
    my_profile_get_schema = extend_schema(
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="user not authenticated"),
        },
        summary="자기 프로필 조회",
        description="""
            현재 로그인한 사용자의 프로필을 조회합니다.
            닉네임, 프로필 이미지, 커피 생활 방식, 팔로워 수, 팔로잉 수, 게시글 수를 반환합니다.
            담당자 : hwstar1204
         """,
        tags=[Profile_Tag],
    )

    my_profile_patch_schema = extend_schema(
        request=UserUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        summary="자기 프로필 수정",
        description="""
            현재 로그인한 사용자의 프로필을 수정합니다.
            닉네임, 프로필 이미지, 소개, 프로필 링크, 커피 생활 방식, 선호하는 커피 맛, 자격증 여부를 수정합니다.
            담당자 : hwstar1204
        """,
        tags=[Profile_Tag],
    )

    my_profile_schema_view = extend_schema_view(get=my_profile_get_schema, patch=my_profile_patch_schema)


class OtherProfileSchema:
    other_proflie_get_schema = extend_schema(
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="user not authenticated"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="상대 프로필 조회",
        description="""
            특정 사용자의 프로필을 조회합니다.
            닉네임, 프로필 이미지, 커피 생활 방식, 팔로워 수, 팔로잉 수, 게시글 수를 반환합니다.
            요청한 사용자가 상대를 팔로우 중인지, 차단 중인지 여부도 반환합니다.
            (팔로우와 차단관계는 공존할 수 없습니다.)
            담당자 : hwstar1204
        """,
        tags=[Profile_Tag],
    )

    other_proflie_schema_view = extend_schema_view(get=other_proflie_get_schema)


class FollowListSchema:
    follow_list_get_schema = extend_schema(
        parameters=[PageNumberSerializer, OpenApiParameter(name="type", type=str, enum=["following", "follower"])],
        responses={
            200: UserFollowListSerializer(many=True),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="자신의 팔로잉/팔로워 프로필 조회",
        description="""
            사용자의 팔로잉/팔로워 리스트를 조회합니다.
            type 파라미터로 팔로잉/팔로워 리스트를 구분합니다.
            notice : 페이지네이션 query parameter를 사용할 수 있습니다.
            담당자 : hwstar1204
        """,
        tags=[Follow_Tag],
    )

    follow_list_schema_view = extend_schema_view(get=follow_list_get_schema)


class FollowListCreateDeleteSchema:
    follow_list_create_delete_get_schema = extend_schema(
        parameters=[PageNumberSerializer, OpenApiParameter(name="type", type=str, enum=["following", "follower"])],
        responses={
            200: UserFollowListSerializer(many=True),
            400: OpenApiResponse(description="Bad Request"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="사용자의 팔로잉/팔로워 리스트 조회",
        description="""
            특정 사용자의 팔로잉/팔로워 리스트를 조회합니다.
            id 파라미터로 사용자의 id를 받고, type 파라미터로 팔로잉/팔로워 리스트를 구분합니다.
            notice : 페이지네이션 query parameter를 사용할 수 있습니다.
            담당자 : hwstar1204
        """,
        tags=[Follow_Tag],
    )

    follow_list_create_delete_post_schema = extend_schema(
        responses={
            201: OpenApiResponse(description="success follow"),
            403: OpenApiResponse(description="user is blocking or blocked"),
            409: OpenApiResponse(description="user is already following"),
        },
        summary="팔로우",
        description="""
            특정 사용자를 팔로우합니다.
            notie : 차단 관계에서 팔로우를 시도하면 403 에러가 발생합니다.
            담당자 : hwstar1204
        """,
        tags=[Follow_Tag],
    )

    follow_list_create_delete_delete_schema = extend_schema(
        responses={
            200: OpenApiResponse(description="success unfollow"),
            404: OpenApiResponse(description="user is not following"),
        },
        summary="팔로우 취소",
        description="""
            특정 사용자의 언팔로우합니다.
            담당자 : hwstar1204
         """,
        tags=[Follow_Tag],
    )

    follow_list_create_delete_schema_view = extend_schema_view(
        get=follow_list_create_delete_get_schema,
        post=follow_list_create_delete_post_schema,
        delete=follow_list_create_delete_delete_schema,
    )


class BlockListSchema:
    block_list_get_schema = extend_schema(
        responses={
            200: UserBlockListSerializer(many=True),
            401: OpenApiResponse(description="user not authenticated"),
        },
        summary="자신의 차단 리스트 조회",
        description="""
            사용자의 차단 리스트를 조회합니다.
            담당자 : hwstar1204
        """,
        tags=[Block_Tag],
    )

    block_list_schema_view = extend_schema_view(get=block_list_get_schema)


class BlockListCreateDeleteSchema:

    block_list_create_delete_post_schema = extend_schema(
        responses={
            201: OpenApiResponse(description="success block"),
            409: OpenApiResponse(description="User is already blocked"),
        },
        summary="차단",
        description="""
            특정 사용자를 차단합니다. (팔로우 관계였다면 팔로우도 강제 취소됩니다.)
            담당자 : hwstar1204
        """,
        tags=[Block_Tag],
    )

    block_list_create_delete_delete_schema = extend_schema(
        responses={
            200: OpenApiResponse(description="success unblock"),
            404: OpenApiResponse(description="User is not blocking"),
        },
        summary="차단 취소",
        description="""
            특정 사용자의 차단을 취소합니다.
            담당자 : hwstar1204
        """,
        tags=[Block_Tag],
    )

    block_list_create_delete_schema_view = extend_schema_view(
        post=block_list_create_delete_post_schema,
        delete=block_list_create_delete_delete_schema,
    )


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


class UserPostListSchema:
    user_post_list_get_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="subject",
                type=str,
                enum=[choice[0] for choice in Post.SUBJECT_TYPE_CHOICES],
                description="게시글 주제",
            ),
        ],
        summary="유저 게시글 조회",
        description="특정 사용자의 게시글을 주제별로 조회합니다.",
        responses={
            200: UserPostSerializer(many=True),
            404: OpenApiResponse(description="Not Found"),
        },
        tags=[Profile_Records_Tag],
    )

    user_post_list_schema_view = extend_schema_view(get=user_post_list_get_schema)


class UserTastedRecordListSchema:
    user_tasted_record_list_get_schema = extend_schema(
        parameters=[
            OpenApiParameter(name="bean_type", type=str, enum=["single", "blend"], required=False),
            OpenApiParameter(
                name="origin_country",
                type=str,
                enum=[
                    "케냐",
                    "과테말라",
                    "에티오피아",
                    "브라질",
                    "콜롬비아",
                    "인도네시아",
                    "온두라스",
                    "탄자니아",
                    "르완다",
                ],
                required=False,
            ),
            OpenApiParameter(name="star_min", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="star_max", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="is_decaf", type=bool, enum=[True, False], required=False),
            OpenApiParameter(name="ordering", type=str, enum=["-created_at", "-taste_review__star", "-likes"], required=False),
        ],
        responses={
            200: UserTastedRecordSerializer(many=True),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="유저 시음기록 리스트 조회",
        description="특정 사용자의 시음기록 리스트를 필터링하여 조회합니다.",
        tags=[Profile_Records_Tag],
    )

    user_tasted_record_list_schema_view = extend_schema_view(get=user_tasted_record_list_get_schema)


class UserBeanListSchema:
    user_bean_list_get_schema = extend_schema(
        responses={
            200: UserBeanSerializer(many=True),
            404: OpenApiResponse(description="Not Found"),
        },
        parameters=[
            OpenApiParameter(name="bean_type", type=str, enum=["single", "blend"]),
            OpenApiParameter(
                name="origin_country",
                type=str,
                enum=[
                    "케냐",
                    "과테말라",
                    "에티오피아",
                    "브라질",
                    "콜비아",
                    "인도네시아",
                    "온두라스",
                    "탄자니아",
                    "르완다",
                ],
                required=False,
            ),
            OpenApiParameter(name="is_decaf", type=bool, enum=[True, False], required=False),
            OpenApiParameter(name="avg_star_min", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="avg_star_max", type=float, enum=[x / 2 for x in range(11)], required=False),
            OpenApiParameter(name="roast_point_min", type=int, enum=range(0, 6), required=False),
            OpenApiParameter(name="roast_point_max", type=int, enum=range(0, 6), required=False),
            OpenApiParameter(
                name="ordering",
                type=str,
                enum=["-note__created_at", "-avg_star", "-tasted_records_cnt"],
                required=False,
            ),
        ],
        summary="유저 찜한 원두 리스트 조회",
        description="""
            특정 사용자가 저장한 원두 리스트를 조회합니다.
            필터링: 원두 종류, 원산지, 디카페인 여부, 평균 별점, 로스팅
            정렬: 노트 생성일, 평균 별점, 시음기록 수
            담당자 : hwstar1204
        """,
        tags=[Profile_Records_Tag],
    )

    user_bean_list_schema_view = extend_schema_view(get=user_bean_list_get_schema)


class UserNoteSchema:
    user_note_get_schema = extend_schema(
        summary="유저 저장한 노트 조회",
        description="특정 사용자의 저장한 노트를 조회합니다.",
        responses={200: UserNoteSerializer(many=True), 404: OpenApiResponse(description="Not Found")},
        tags=[Profile_Records_Tag],
    )

    user_note_schema_view = extend_schema_view(get=user_note_get_schema)
