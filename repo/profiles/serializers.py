from rest_framework import serializers

from repo.profiles.models import CustomUser, Relationship


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["nickname", "social_id"]

    def create(self, validated_data):
        user = CustomUser(
            nickname=validated_data["nickname"],
            social_id=validated_data["social_id"],
            login_type="kakao",
        )
        user.set_password(None)
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.nickname = validated_data.get("nickname", instance.nickname)
        instance.save()
        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "nickname", "profile_image"]


class BudyRecommendSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer()
    follower_cnt = serializers.IntegerField()

    class Meta:
        model = CustomUser
        fields = ["user", "follower_cnt"]
