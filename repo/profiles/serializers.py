from rest_framework import serializers

from repo.profiles.models import CustomUser, UserDetail
from repo.profiles.validators import UserValidator


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["nickname", "social_id"]

    def create(self, validated_data):
        user = CustomUser(
            nickname=validated_data["nickname"],
        )
        user.set_password(None)
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.nickname = validated_data.get("nickname", instance.nickname)
        instance.save()
        return instance


class UserSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["nickname", "gender", "birth"]

    def validate_nickname(self, value):
        return UserValidator.validate_nickname(value, instance=self.instance)

    def validate_gender(self, value):
        if value not in ["남", "여"]:
            raise serializers.ValidationError("성별은 '남' 또는 '여'만 선택 가능합니다.")
        return value

    def validate_birth(self, value):
        if len(str(value)) != 4 or not 1900 <= value <= 2100:
            raise serializers.ValidationError("출생 연도는 4자리 숫자여야 하며, 1900년과 2100년 사이여야 합니다.")
        return value


class UserDetailSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetail
        fields = ["introduction", "profile_link", "coffee_life", "preferred_bean_taste", "is_certificated"]

    coffee_life = serializers.JSONField(
        default={
            "cafe_tour": False,
            "coffee_extraction": False,
            "coffee_study": False,
            "cafe_alba": False,
            "cafe_work": False,
            "cafe_operation": False,
        }
    )

    preferred_bean_taste = serializers.JSONField(default={"body": 3, "acidity": 3, "bitterness": 3, "sweetness": 3})


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"


class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "nickname", "profile_image"]


class UserProfileSerializer(UserSimpleSerializer):
    introduction = serializers.CharField(required=False, default="")
    profile_link = serializers.CharField(required=False, default="")
    coffee_life = serializers.JSONField()
    preferred_bean_taste = serializers.JSONField()
    is_certificated = serializers.BooleanField()
    following_cnt = serializers.IntegerField()
    follower_cnt = serializers.IntegerField()
    post_cnt = serializers.IntegerField()
    is_user_following = serializers.BooleanField(required=False, default=False)
    is_user_blocking = serializers.BooleanField(required=False, default=False)

    class Meta(UserSimpleSerializer.Meta):
        fields = UserSimpleSerializer.Meta.fields + [
            "introduction",
            "profile_link",
            "coffee_life",
            "preferred_bean_taste",
            "is_certificated",
            "following_cnt",
            "follower_cnt",
            "post_cnt",
            "is_user_following",
            "is_user_blocking",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDetail
        fields = ["introduction", "profile_link", "coffee_life", "preferred_bean_taste", "is_certificated"]


class UserUpdateSerializer(serializers.ModelSerializer):
    user_detail = UserDetailSerializer(required=False)
    nickname = serializers.CharField(required=False, allow_blank=True)

    def validate_nickname(self, value):
        UserValidator.validate_nickname(value, instance=self.instance)
        return value

    class Meta:
        model = CustomUser
        fields = ["nickname", "user_detail"]
