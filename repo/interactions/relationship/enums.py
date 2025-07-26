from enum import Enum


class RelationshipType(Enum):
    """관계 유형을 정의하는 Enum 클래스"""

    FOLLOW = ("follow", "팔로우")
    BLOCK = ("block", "차단")

    @classmethod
    def choices(cls):
        """Django 모델 필드에서 사용할 수 있는 choices 형태로 반환"""
        return [(member.name, member.display_name) for member in cls]

    @classmethod
    def values(cls):
        """모든 값들을 리스트로 반환"""
        return [member.name for member in cls]

    @property
    def name(self):
        return self.value[0]

    @property
    def display_name(self):
        return self.value[1]
