from django.db import models


class EventStatus(models.TextChoices):
    """이벤트 상태"""

    READY = "ready", "진행 전"
    ACTIVE = "active", "진행 중"
    DONE = "done", "종료"


class EventType(models.TextChoices):
    """이벤트 타입"""

    INTERNAL = "internal", "내부 조건형"
    PROMOTIONAL = "promotional", "프로모션"
