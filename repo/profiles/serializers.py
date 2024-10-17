from rest_framework import serializers

from repo.profiles.models import CustomUser, Relationship, UserDetail


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


class UserProfileSerializer(UserSimpleSerializer):
    coffee_life = serializers.JSONField()
    following_cnt = serializers.IntegerField()
    follower_cnt = serializers.IntegerField()
    post_cnt = serializers.IntegerField()
    is_user_following = serializers.BooleanField(required=False)

    class Meta(UserSimpleSerializer.Meta):
        fields = UserSimpleSerializer.Meta.fields + ["coffee_life", "following_cnt", "follower_cnt", "post_cnt", "is_user_following"]


class UserFollowListSerializer(UserSimpleSerializer):
    is_following = serializers.BooleanField()

    class Meta(UserSimpleSerializer.Meta):
        fields = UserSimpleSerializer.Meta.fields + ["is_following"]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetail
        fields = ["introduction", "profile_link", "coffee_life", "preferred_bean_taste", "is_certificated"]


class UserUpdateSerializer(serializers.ModelSerializer):
    user_detail = UserDetailSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = ["nickname", "profile_image", "user_detail"]


class BudyRecommendSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer()
    follower_cnt = serializers.IntegerField()

    class Meta:
        model = CustomUser
        fields = ["user", "follower_cnt"]
