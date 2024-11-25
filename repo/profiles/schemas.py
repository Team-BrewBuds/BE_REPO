from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.profiles.serializers import (
    UserProfileSerializer,
    UserUpdateSerializer,
)
from repo.records.models import Post
from repo.records.posts.serializers import UserPostSerializer
from repo.records.serializers import UserNoteSerializer
from repo.records.tasted_record.serializers import UserTastedRecordSerializer

Profile_Tag = "profiles"
Profile_Records_Tag = "profile_records"


class ProfileSchema:
    my_profile_get_schema = extend_schema(
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description="user not authenticated"),
            404: OpenApiResponse(description="user not found"),
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
            401: OpenApiResponse(description="user not authenticated"),
        },
        summary="자기 프로필 수정",
        description="""
            현재 로그인한 사용자의 프로필을 수정합니다.
            닉네임, 프로필 이미지, 소개, 프로필 링크, 커피 생활 방식, 선호하는 커피 맛, 자격증 여부를 수정합니다.
            notice : 닉네임 유효성 검사 추가
            - 중복, 공백 불가
            - 2 ~ 12자의 한글 또는 숫자
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
            404: OpenApiResponse(description="user not found"),
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
        description="특정 사용자의 게시글을 주제별로 조회합니다. (정렬 기준: 최신순)",
        responses={
            200: UserPostSerializer(many=True),
            400: OpenApiResponse(description="Invalid subject parameter"),
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


class UserNoteSchema:
    user_note_get_schema = extend_schema(
        summary="유저 저장한 노트 조회",
        description="특정 사용자의 저장한 노트를 조회합니다.",
        responses={200: UserNoteSerializer(many=True), 404: OpenApiResponse(description="Not Found")},
        tags=[Profile_Records_Tag],
    )

    user_note_schema_view = extend_schema_view(get=user_note_get_schema)
