from enum import Enum


class Topic(Enum):
    POST = ("post", "게시물")
    TASTED_RECORD = ("tasted_record", "시음 기록")

    def get_topic_id(self, object_id: int) -> str:
        """
        주어진 object_id로 토픽 ID 문자열을 생성합니다.
        생성된 토픽 ID 문자열 (예: "post_123")
        """
        return f"{self.value[0]}_{object_id}"

    @property
    def get_topic_type(self) -> str:
        return self.value[0]

    @property
    def get_topic_name(self) -> str:
        return self.value[1]


# example
# topic = Topic.POST
# topic_id = topic.get_topic_id(123)  # "post_123" 반환
