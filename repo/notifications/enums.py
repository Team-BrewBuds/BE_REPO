from enum import Enum
from typing import NamedTuple


class TopicData(NamedTuple):
    type: str
    display_name: str


class Topic(Enum):
    POST = TopicData("post", "게시물")
    TASTED_RECORD = TopicData("tasted_record", "시음 기록")

    @property
    def type(self) -> str:
        """토픽 타입을 반환"""
        return self.value.type

    @property
    def display_name(self) -> str:
        """토픽 이름을 반환"""
        return self.value.display_name

    def topic_id(self, object_id: int) -> str:
        """주어진 object_id를 포함한 토픽 ID 생성"""
        return f"{self.type}_{object_id}"
