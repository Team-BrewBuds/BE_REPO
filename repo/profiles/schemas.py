from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.profiles.serializers import (
    UserAccountSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)
from repo.records.serializers import UserNoteSerializer

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
        examples=[
            OpenApiExample(
                "Profile Update Example",
                value={
                    "nickname": "커피러버",
                    "user_detail": {
                        "introduction": "커피를 사랑하는 사람입니다",
                        "profile_link": "https://example.com/profile",
                        "coffee_life": {
                            "cafe_alba": True,
                            "cafe_tour": False,
                            "cafe_work": False,
                            "coffee_study": False,
                            "cafe_operation": False,
                            "coffee_extraction": True,
                        },
                        "preferred_bean_taste": {"body": 4, "acidity": 3, "sweetness": 5, "bitterness": 2},
                        "is_certificated": True,
                    },
                },
                request_only=True,
            )
        ],
        summary="자기 프로필 수정",
        description="""
            현재 로그인한 사용자의 프로필을 수정합니다.
            닉네임, 프로필 이미지, 소개, 프로필 링크, 커피 생활 방식, 선호하는 커피 맛, 자격증 여부를 수정합니다.

            Notice
            1.닉네임 유효성 검사
            - 중복, 공백 불가
            - 2 ~ 12자의 한글 또는 숫자

            2.coffee_life와 preferred_bean_taste는 JSON 객체 형태로 전달해야 합니다
            - coffee_life: 각 항목(cafe_tour, coffee_extraction 등)에 대해 true/false 값을 가진 객체
            - preferred_bean_taste: 각 맛(body, acidity 등)에 대해 1~5 사이의 숫자 값을 가진 객체
            담당자 : hwstar1204
        """,
        tags=[Profile_Tag],
    )

    my_profile_delete_schema = extend_schema(
        summary="자기 계정 탈퇴",
        description="""
            현재 로그인한 사용자의 계정을 탈퇴합니다.
        """,
        tags=[Profile_Tag],
    )

    my_profile_schema_view = extend_schema_view(get=my_profile_get_schema, patch=my_profile_patch_schema, delete=my_profile_delete_schema)


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


class UserNoteSchema:
    user_note_get_schema = extend_schema(
        summary="유저 저장한 노트 조회",
        description="특정 사용자의 저장한 노트를 조회합니다.",
        responses={200: UserNoteSerializer(many=True), 404: OpenApiResponse(description="Not Found")},
        tags=[Profile_Records_Tag],
    )

    user_note_schema_view = extend_schema_view(get=user_note_get_schema)


class UserAccountSchema:
    user_account_get_schema = extend_schema(
        summary="사용자 계정 정보 조회",
        description="생일과 이메일은 null일 수 있습니다.",
        responses={
            200: UserAccountSerializer,
            401: OpenApiResponse(description="user not authenticated"),
            404: OpenApiResponse(description="user not found"),
        },
        tags=[Profile_Tag],
    )

    user_account_schema_view = extend_schema_view(get=user_account_get_schema)
