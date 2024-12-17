from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer

from .serializers import (
    UserBlockListSerializer,
    UserFollowListSerializer,
)

Follow_Tag = "follow"
Block_Tag = "block"


class FollowListSchema:
    follow_list_get_schema = extend_schema(
        operation_id="interactions_relationship_my_follow_list",
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
            notice : 페이지네이션 query parameter를 사용할 수 있습니다, 정렬 기준은 최근 관계 설정 순입니다.
            담당자 : hwstar1204
        """,
        tags=[Follow_Tag],
    )

    follow_list_schema_view = extend_schema_view(get=follow_list_get_schema)


class FollowListCreateDeleteSchema:
    follow_list_create_delete_get_schema = extend_schema(
        operation_id="interactions_relationship_user_follow_list",
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
            notice : 정렬 기준은 최근 차단 관계 설정 순입니다.
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
