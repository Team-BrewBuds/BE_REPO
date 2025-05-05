from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.common.serializers import PageNumberSerializer
from repo.records.models import Post
from repo.records.posts.serializers import (
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    TopPostSerializer,
    UserPostSerializer,
)

Post_Tag = "Post"


class PostSchema:
    post_list_get_schema = extend_schema(
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="subject",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="subject filter",
                enum=[choice[0] for choice in Post.SUBJECT_TYPE_CHOICES],
                required=False,
            ),
        ],
        responses={200: PostListSerializer},
        summary="홈 [게시글] 피드 조회",
        description="""
            홈 피드의 주제별 게시글 list 데이터를 가져옵니다.
            - 순서: 팔로잉, 일반
            - 정렬: 최신순
            - 페이지네이션 적용 (12개)
            - 30분이내 조회하지않은 게시글만 가져옵니다.

            Notice:
            - like_cnt에서 likes로 변경
            - comments(댓글 수), is_user_noted(사용자 저장여부) 추가 됨
            - 비회원일경우 랜덤으로 게시글을 가져옵니다. (subject 쿼리 파라미터 미사용)
            - 주제 (default: 전체)
            : normal(일반), cafe(카페), bean(원두), info(정보), question(질문), worry(고민), gear(장비)
        """,
        tags=[Post_Tag],
    )

    post_list_post_schema = extend_schema(
        request=PostCreateUpdateSerializer,
        responses={201: PostDetailSerializer, 400: OpenApiResponse(description="Bad Request")},
        summary="게시글 생성",
        description="""
            단일 게시글을 생성합니다. (사진과 시음기록은 함께 등록할 수 없습니다.)
            태그는 , 로 구분하여 문자열로 요청해주세요.
            로그인한 유저만 게시글 생성 가능
        """,
        tags=[Post_Tag],
    )

    post_list_create_schema_view = extend_schema_view(get=post_list_get_schema, post=post_list_post_schema)

    post_detail_get_schema = extend_schema(
        responses={200: PostDetailSerializer},
        summary="게시글 상세 조회",
        description="게시글의 상세 정보를 가져옵니다.",
        tags=[Post_Tag],
    )

    post_detail_put_schema = extend_schema(
        request=PostCreateUpdateSerializer,
        responses={200: PostCreateUpdateSerializer, 400: OpenApiResponse(description="Bad Request")},
        summary="게시글 수정",
        description="""
            게시글의 정보를 수정합니다.
            tasted_record, photo는 id로 수정합니다.
            notice : 수정 권한은 작성자에게만 허용합니다.
        """,
        tags=[Post_Tag],
    )

    post_detail_patch_schema = extend_schema(
        request=PostCreateUpdateSerializer,
        responses={200: PostCreateUpdateSerializer, 400: OpenApiResponse(description="Bad Request")},
        summary="게시글 수정",
        description="""
            게시글의 정보를 수정합니다.
            tasted_record, photo는 id로 수정합니다.
            notice : 수정 권한은 작성자에게만 허용합니다.
        """,
        tags=[Post_Tag],
    )

    post_detail_delete_schema = extend_schema(
        responses={204: OpenApiResponse(description="No Content")},
        summary="게시글 삭제",
        description="""
            게시글을 삭제합니다.
            notice : 삭제 권한은 작성자에게만 허용합니다.
        """,
        tags=[Post_Tag],
    )

    post_detail_schema_view = extend_schema_view(
        get=post_detail_get_schema,
        put=post_detail_put_schema,
        patch=post_detail_patch_schema,
        delete=post_detail_delete_schema,
    )

    user_post_list_get_schema = extend_schema(
        parameters=[
            PageNumberSerializer,
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
        tags=[Post_Tag],
    )

    user_post_list_schema_view = extend_schema_view(get=user_post_list_get_schema)

    top_posts_get_schema = extend_schema(
        responses={200: TopPostSerializer},
        summary="인기 게시글 조회",
        description="""
            홈 [전체] - 주제별 지난주 조회수 상위 60개 인기 게시글 조회 API
            - 정렬: 조회수
            - 페이지네이션 적용

            notice:
            - 필드명 변경 (like_cnt -> likes, comment_cnt -> comments)
            - 필드 추가 (created_at, view_cnt)
            - 차단 유저의 게시글은 제외합니다.
            - 비회원일 경우 예외 처리합니다. (subject 쿼리 파라미터 미사용)
            - 주제 (default: 전체)
            : normal(일반), cafe(카페), bean(원두), info(정보), question(질문), worry(고민), gear(장비)
        """,
        tags=[Post_Tag],
        parameters=[
            PageNumberSerializer,
            OpenApiParameter(
                name="subject",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="subject filter",
                enum=[choice[0] for choice in Post.SUBJECT_TYPE_CHOICES],
            ),
        ],
    )

    top_posts_schema_view = extend_schema_view(get=top_posts_get_schema)
