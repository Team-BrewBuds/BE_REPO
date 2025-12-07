from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from repo.events.enums import EventStatus, EventType
from repo.events.serializers import (
    EventCompleteRequestSerializer,
    EventCompletionResponseSerializer,
    EventCompletionSerializer,
    UnifiedEventSerializer,
)

EventsTag = "events"


class EventListSchema:
    """이벤트 목록 조회 스키마"""

    event_list_get_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="event_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="이벤트 타입 필터 (내부조건형, 프로모션)",
                required=False,
                enum=[choice[0] for choice in EventType.choices],
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="이벤트 상태 필터 (진행 전, 진행 중, 종료)",
                required=False,
                enum=[choice[0] for choice in EventStatus.choices],
            ),
        ],
        responses={
            200: UnifiedEventSerializer(many=True),
            401: OpenApiResponse(description="Unauthorized"),
        },
        summary="통합 이벤트 목록 조회",
        description="""
            진행 중인 이벤트 목록을 조회합니다.

            - event_type 파라미터가 없으면 모든 타입의 이벤트를 조회합니다.
            - event_type=promotional: 프로모션 이벤트만 조회
            - event_type=internal: 내부 조건형 이벤트만 조회
            - 각 이벤트에 사용자의 완료 여부(is_completed)가 포함됩니다.
            - 프로모션 이벤트는 현재 진행 기간 내의 이벤트만 조회됩니다.

            담당자: hwstar1204
        """,
        tags=[EventsTag],
    )

    event_list_schema_view = extend_schema_view(get=event_list_get_schema)


class EventDetailSchema:
    """이벤트 상세 조회 스키마"""

    event_detail_get_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="event_key",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="이벤트 키",
                required=True,
            ),
            OpenApiParameter(
                name="event_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="이벤트 타입 필터 (내부조건형, 프로모션)",
                required=True,
                enum=[choice[0] for choice in EventType.choices],
            ),
        ],
        responses={
            200: UnifiedEventSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
        summary="이벤트 상세 조회",
        description="""
            특정 이벤트의 상세 정보를 조회합니다.

            - 이벤트 타입(프로모션/내부)은 자동으로 판별됩니다.
            - 사용자의 완료 여부(is_completed)가 포함됩니다.

            담당자: hwstar1204
        """,
        tags=[EventsTag],
    )

    event_detail_schema_view = extend_schema_view(get=event_detail_get_schema)


class EventCompleteSchema:
    """Webhook 이벤트 완료 기록 스키마"""

    event_complete_post_schema = extend_schema(
        request=EventCompleteRequestSerializer,
        responses={
            201: EventCompletionResponseSerializer,
            400: OpenApiResponse(description="Bad Request - 검증 실패 (사용자 없음, 중복 참여 등)"),
            403: OpenApiResponse(description="Forbidden - API Key 인증 실패"),
            404: OpenApiResponse(description="Not Found - 이벤트를 찾을 수 없음"),
        },
        summary="Webhook 이벤트 참여 완료 기록",
        description="""
            Walla webhook을 통한 프로모션 이벤트 참여 완료를 기록합니다.

            **인증**: X-API-Key 헤더에 시스템 API Key 필요
            **프로모션 이벤트만 허용됩니다.**

            요청 Body:
            - projectKey: projectID (이벤트 식별)
            - email: 사용자 이메일
            - timestamp: 완료 시간
            - is_agree: 사용자 동의 여부
            - 기타 필드: 폼 제출 내용 (content로 저장)

            검증 사항:
            - 사용자 이메일: 존재하는 사용자만 가능 (400)
            - 이벤트 상태: 진행 중(active)인 이벤트만 가능 (400)
            - 이벤트 기간: 현재 시간이 이벤트 기간 내여야 함 (400)
            - 중복 참여: 이미 완료한 이벤트는 재참여 불가 (400)

            담당자: hwstar1204
        """,
        tags=[EventsTag],
    )

    event_complete_schema_view = extend_schema_view(post=event_complete_post_schema)


class MyCompletionListSchema:
    """내 참여 이력 조회 스키마"""

    my_completion_list_get_schema = extend_schema(
        parameters=[
            OpenApiParameter(
                name="event_type",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="이벤트 타입 필터 (promotional, internal)",
                required=False,
                enum=["promotional", "internal"],
            ),
        ],
        responses={
            200: EventCompletionSerializer(many=True),
            401: OpenApiResponse(description="Unauthorized"),
        },
        summary="내 이벤트 참여 이력 조회",
        description="""
            현재 사용자가 완료한 이벤트 목록을 조회합니다.

            - event_type 파라미터가 없으면 모든 타입의 완료 이력을 조회합니다.
            - event_type=promotional: 프로모션 이벤트 완료 이력만 조회
            - event_type=internal: 내부 이벤트 완료 이력만 조회
            - 완료 시간 기준 최신순으로 정렬됩니다.

            담당자: hwstar1204
        """,
        tags=[EventsTag],
    )

    my_completion_list_schema_view = extend_schema_view(get=my_completion_list_get_schema)
