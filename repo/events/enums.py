from enum import Enum, StrEnum


class EventStatus(StrEnum):
    """이벤트 상태"""

    READY = "ready"
    ACTIVE = "active"
    DONE = "done"

    @classmethod
    def values(cls) -> list[str]:
        return [choice.value for choice in cls]


class EventType(Enum):
    INTERNAL = "internal"
    PROMOTIONAL = "promotional"

    @property
    def type(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        return self.value
