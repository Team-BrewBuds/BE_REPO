from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from repo.events.enums import EventType
from repo.events.models import EventCompletion, InternalEvent, PromotionalEvent
from repo.profiles.models import CustomUser


class EventService:
    """이벤트 관련 비즈니스 로직"""

    def get_active_events(
        self, user: CustomUser | None = None, event_type: EventType | None = None
    ) -> list[PromotionalEvent | InternalEvent]:
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
            promotional_queryset = PromotionalEvent.objects.filter(
                status="active",
                start_date__lte=now,
                end_date__gte=now,
            )
            promotional_queryset = self._annotate_completion_status(promotional_queryset, user, "promotional_event")
            events.extend(list(promotional_queryset))

        # 내부 이벤트 조회
        if event_type is None or event_type == EventType.INTERNAL.value:
            internal_queryset = InternalEvent.objects.filter(status="active")
            internal_queryset = self._annotate_completion_status(internal_queryset, user, "internal_event")
            events.extend(list(internal_queryset))

        return events

    def get_event_by_key(self, event_key, user):
        """
        id로 이벤트 조회 (타입 자동 판별)

        Args:
            event_key: 이벤트 키
            user: 현재 사용자

        Returns:
            이벤트 객체 (PromotionalEvent 또는 InternalEvent)

        Raises:
            NotFound: 이벤트를 찾을 수 없는 경우
        """
        # 프로모션 이벤트 확인
        try:
            queryset = PromotionalEvent.objects.filter(event_key=event_key)
            queryset = self._annotate_completion_status(queryset, user, "promotional_event")
            return queryset.get()
        except PromotionalEvent.DoesNotExist:
            pass

        # 내부 이벤트 확인
        try:
            queryset = InternalEvent.objects.filter(event_key=event_key)
            queryset = self._annotate_completion_status(queryset, user, "internal_event")
            return queryset.get()
        except InternalEvent.DoesNotExist:
            pass

        raise NotFound("이벤트를 찾을 수 없습니다.")

    def complete_event(self, event_key, user):
        """
        이벤트 완료 처리 (프로모션만 허용, 검증 포함)

        Args:
            event_key: 이벤트 키
            user: 현재 사용자

        Returns:
            EventCompletion: 생성된 완료 기록

        Raises:
            NotFound: 이벤트를 찾을 수 없는 경우
            ValidationError: 검증 실패 (타입, 상태, 기간, 중복)
        """
        # 이벤트 타입 판별
        event_type, event = self._determine_event_type(event_key)

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
        if self.is_event_completed_by_user(event_key, user):
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

        if event_type == EventType.PROMOTIONAL.value:
            queryset = queryset.filter(promotional_event__isnull=False)
        elif event_type == EventType.INTERNAL.value:
            queryset = queryset.filter(internal_event__isnull=False)

        return queryset.order_by("-completed_at")

    def is_event_completed_by_user(self, event_key, user):
        """
        완료 여부 확인

        Args:
            event_key: 이벤트 키
            user: 현재 사용자

        Returns:
            bool: 완료 여부
        """
        return EventCompletion.objects.filter(
            Q(promotional_event__event_key=event_key) | Q(internal_event__event_key=event_key),
            user=user,
        ).exists()

    def _determine_event_type(self, event_key):
        """
        이벤트 타입 판별 헬퍼 메서드

        Args:
            event_key: 이벤트 키

        Returns:
            tuple: (EventType, 이벤트 객체)

        Raises:
            NotFound: 이벤트를 찾을 수 없는 경우
        """
        try:
            event = PromotionalEvent.objects.get(event_key=event_key)
            return EventType.PROMOTIONAL, event
        except PromotionalEvent.DoesNotExist:
            pass

        try:
            event = InternalEvent.objects.get(event_key=event_key)
            return EventType.INTERNAL, event
        except InternalEvent.DoesNotExist:
            pass

        raise NotFound("이벤트를 찾을 수 없습니다.")

    def complete_event_webhook(self, project_key: str, email: str, timestamp, is_agree: bool, content: dict):
        """
        Webhook을 통한 이벤트 완료 처리 (프로모션 전용)

        Args:
            project_key: Walla projectID (이벤트 식별)
            email: 사용자 이메일
            timestamp: 완료 시간
            is_agree: 사용자 동의 여부
            content: 폼 제출 내용

        Returns:
            EventCompletion: 생성된 완료 기록

        Raises:
            ValidationError: 사용자를 찾을 수 없거나 검증 실패
            NotFound: 이벤트를 찾을 수 없는 경우
        """
        # 사용자 조회
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist as e:
            raise ValidationError(f"이메일 '{email}'에 해당하는 사용자를 찾을 수 없습니다.") from e

        # 프로모션 이벤트 조회
        try:
            event = PromotionalEvent.objects.get(event_key=project_key)
        except PromotionalEvent.DoesNotExist as e:
            raise NotFound(f"이벤트 키 '{project_key}'에 해당하는 이벤트를 찾을 수 없습니다.") from e

        # 이벤트 상태 검증
        if event.status != "active":
            raise ValidationError("진행 중인 이벤트가 아닙니다.")

        # 이벤트 기간 검증
        now = timezone.now()
        if not (event.start_date <= now <= event.end_date):
            raise ValidationError("이벤트 기간이 아닙니다.")

        # 중복 참여 검증
        if EventCompletion.objects.filter(user=user, promotional_event=event).exists():
            raise ValidationError("이미 참여 완료한 이벤트입니다.")

        # 완료 기록 생성
        completion = EventCompletion.objects.create(
            user=user,
            promotional_event=event,
            is_agree=is_agree,
            content=content,
            completed_at=timestamp,
        )

        return completion

    def _annotate_completion_status(self, queryset, user: CustomUser | None, event_field: str):
        """
        이벤트 완료 여부를 annotation으로 추가하는 헬퍼 메서드

        Args:
            queryset: 이벤트 QuerySet
            user: 현재 사용자 (None이면 비회원)
            event_field: 'promotional_event' 또는 'internal_event'

        Returns:
            완료 여부가 annotation된 QuerySet
        """
        if user is None or user.is_anonymous:
            return queryset.annotate(is_completed=Value(False, output_field=BooleanField()))

        return queryset.annotate(is_completed=Exists(EventCompletion.objects.filter(user=user, **{event_field: OuterRef("event_key")})))
