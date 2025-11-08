from enum import Enum


class EventType(Enum):
    INTERNAL = "internal"
    PROMOTIONAL = "promotional"

    @property
    def type(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        return self.value
