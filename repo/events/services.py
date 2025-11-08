from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from repo.events.enums import EventType
from repo.events.models import EventCompletion, InternalEvent, PromotionalEvent


class EventService:
    """이벤트 관련 비즈니스 로직"""

    def get_active_events(self, user, event_type=None):
        """
        진행 중인 이벤트 목록 조회 + 사용자 완료 여부

        Args:
            user: 현재 사용자
            event_type: 'promotional' 또는 'internal' (None이면 전체 조회)

        Returns:
            list: 통합된 이벤트 목록 (프로모션 + 내부)
        """
        now = timezone.now()
        events = []

        # 프로모션 이벤트 조회
        if event_type is None or event_type == EventType.PROMOTIONAL.value:
            promotional_events = PromotionalEvent.objects.filter(
                status="active",
                start_date__lte=now,
                end_date__gte=now,
            ).annotate(
                is_completed=Exists(
                    EventCompletion.objects.filter(
                        user=user,
                        promotional_event=OuterRef("event_key"),
                    )
                )
            )
            events.extend(list(promotional_events))

        # 내부 이벤트 조회
        if event_type is None or event_type == EventType.INTERNAL.value:
            internal_events = InternalEvent.objects.filter(status="active").annotate(
                is_completed=Exists(
                    EventCompletion.objects.filter(
                        user=user,
                        internal_event=OuterRef("event_key"),
                    )
                )
            )
            events.extend(list(internal_events))

        return events

    def get_event_by_id(self, event_id, user):
        """
        id로 이벤트 조회 (타입 자동 판별)

        Args:
            event_id: 이벤트 UUID
            user: 현재 사용자

        Returns:
            이벤트 객체 (PromotionalEvent 또는 InternalEvent)

        Raises:
            NotFound: 이벤트를 찾을 수 없는 경우
        """
        # 프로모션 이벤트 확인
        try:
            event = PromotionalEvent.objects.annotate(
                is_completed=Exists(
                    EventCompletion.objects.filter(
                        user=user,
                        promotional_event=OuterRef("event_key"),
                    )
                )
            ).get(event_key=event_id)
            return event
        except PromotionalEvent.DoesNotExist:
            pass

        # 내부 이벤트 확인
        try:
            event = InternalEvent.objects.annotate(
                is_completed=Exists(
                    EventCompletion.objects.filter(
                        user=user,
                        internal_event=OuterRef("event_key"),
                    )
                )
            ).get(event_key=event_id)
            return event
        except InternalEvent.DoesNotExist:
            pass

        raise NotFound("이벤트를 찾을 수 없습니다.")

    def complete_event(self, event_id, user):
        """
        이벤트 완료 처리 (프로모션만 허용, 검증 포함)

        Args:
            event_id: 이벤트 UUID
            user: 현재 사용자

        Returns:
            EventCompletion: 생성된 완료 기록

        Raises:
            NotFound: 이벤트를 찾을 수 없는 경우
            ValidationError: 검증 실패 (타입, 상태, 기간, 중복)
        """
        # 이벤트 타입 판별
        event_type, event = self._determine_event_type(event_id)

        # 내부 이벤트는 수동 완료 불가
        if event_type == EventType.INTERNAL:
            raise ValidationError("내부 이벤트는 수동 완료할 수 없습니다.")

        # 이벤트 상태 검증
        if event.status != "active":
            raise ValidationError("진행 중인 이벤트가 아닙니다.")

        # 이벤트 기간 검증
        now = timezone.now()
        if not (event.start_date <= now <= event.end_date):
            raise ValidationError("이벤트 기간이 아닙니다.")

        # 중복 참여 검증
        if self.is_event_completed_by_user(event_id, user):
            raise ValidationError("이미 참여 완료한 이벤트입니다.")

        # 완료 기록 생성
        completion = EventCompletion.objects.create(
            user=user,
            promotional_event=event,
        )

        return completion

    def get_user_completions(self, user, event_type=None):
        """
        사용자의 완료 이력 조회

        Args:
            user: 현재 사용자
            event_type: 'promotional' 또는 'internal' (None이면 전체 조회)

        Returns:
            QuerySet: 완료 기록 목록
        """
        queryset = EventCompletion.objects.filter(user=user).select_related(
            "promotional_event",
            "internal_event",
        )

        # 타입별 필터링
        if event_type == EventType.PROMOTIONAL.value:
            queryset = queryset.filter(promotional_event__isnull=False)
        elif event_type == EventType.INTERNAL.value:
            queryset = queryset.filter(internal_event__isnull=False)

        return queryset.order_by("-completed_at")

    def is_event_completed_by_user(self, event_id, user):
        """
        완료 여부 확인

        Args:
            event_id: 이벤트 UUID
            user: 현재 사용자

        Returns:
            bool: 완료 여부
        """
        return EventCompletion.objects.filter(
            Q(promotional_event__event_key=event_id) | Q(internal_event__event_key=event_id),
            user=user,
        ).exists()

    def _determine_event_type(self, event_id):
        """
        이벤트 타입 판별 헬퍼 메서드

        Args:
            event_id: 이벤트 UUID

        Returns:
            tuple: (EventType, 이벤트 객체)

        Raises:
            NotFound: 이벤트를 찾을 수 없는 경우
        """
        # 프로모션 이벤트 확인
        try:
            event = PromotionalEvent.objects.get(event_key=event_id)
            return EventType.PROMOTIONAL, event
        except PromotionalEvent.DoesNotExist:
            pass

        # 내부 이벤트 확인
        try:
            event = InternalEvent.objects.get(event_key=event_id)
            return EventType.INTERNAL, event
        except InternalEvent.DoesNotExist:
            pass

        raise NotFound("이벤트를 찾을 수 없습니다.")
