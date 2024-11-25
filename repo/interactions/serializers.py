from rest_framework import serializers

from repo.profiles.serializers import UserSimpleSerializer


class UserFollowListSerializer(serializers.Serializer):
    user = UserSimpleSerializer()
    is_following = serializers.BooleanField()


class UserBlockListSerializer(serializers.Serializer):
    user = UserSimpleSerializer(source="to_user")

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation["user"]
