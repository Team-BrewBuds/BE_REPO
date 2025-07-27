from rest_framework import serializers

from repo.profiles.serializers import UserSimpleSerializer


class UserFollowListSerializer(serializers.Serializer):
    """팔로잉/팔로워 리스트 조회 시리얼라이저"""

    user = UserSimpleSerializer()
    is_following = serializers.BooleanField()


class UserBlockListSerializer(serializers.Serializer):
    """차단 리스트 조회 시리얼라이저"""

    user = UserSimpleSerializer(source="to_user")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation["user"]
