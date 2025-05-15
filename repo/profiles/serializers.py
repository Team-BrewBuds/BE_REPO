from rest_framework import serializers

from repo.beans.models import Bean
from repo.common.utils import get_time_difference
from repo.profiles.models import CustomUser, UserDetail
from repo.profiles.validators import UserValidator
from repo.records.models import Photo, Post, TastedRecord


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


class UserDetailSignupSerializer(serializers.ModelSerializer):
    coffee_life = serializers.JSONField(required=False, default=UserDetail.default_coffee_life)
    preferred_bean_taste = serializers.JSONField(required=False, default=UserDetail.default_taste)
    is_certificated = serializers.BooleanField(required=False, default=False)

    def validate_coffee_life(self, value):
        valid_keys = UserDetail.COFFEE_LIFE_CHOICES
        for key in value.keys():
            if key not in valid_keys:
                raise serializers.ValidationError(f"유효하지 않은 커피 생활 선택: {key}")
        return value

    def validate_preferred_bean_taste(self, value):
        required_fields = UserDetail.TASTE_CHOICES
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"필수 필드가 누락되었습니다: {field}")
            if not isinstance(value[field], (int, float)) or not 1 <= value[field] <= 5:
                raise serializers.ValidationError(f"{field}는 1에서 5 사이의 숫자여야 합니다.")
        return value

    class Meta:
        model = UserDetail
        fields = ["coffee_life", "preferred_bean_taste", "is_certificated"]


class SignupSerializer(serializers.ModelSerializer):
    detail = UserDetailSignupSerializer(required=False)

    def validate_nickname(self, value):
        return UserValidator.validate_nickname(value)

    def validate_birth(self, value):
        if len(str(value)) != 4 or not 1900 <= value <= 2100:
            raise serializers.ValidationError("출생 연도는 4자리 숫자여야 하며, 1900년과 2100년 사이여야 합니다.")
        return value

    def validate_gender(self, value):
        if value not in ["남", "여"]:
            raise serializers.ValidationError("성별은 '남' 또는 '여'만 선택 가능합니다.")
        return value

    class Meta:
        model = CustomUser
        fields = ["nickname", "gender", "birth", "detail"]


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
    tasted_record_cnt = serializers.IntegerField()
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
            "tasted_record_cnt",
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


class UserAccountSerializer(serializers.Serializer):
    joined_at = serializers.CharField()
    joined_duration = serializers.IntegerField()
    login_type = serializers.CharField()
    gender = serializers.CharField()
    birth_year = serializers.IntegerField(required=False)
    email = serializers.CharField(required=False)


class PrefSummarySerializer(serializers.Serializer):
    tasted_record_cnt = serializers.IntegerField()
    post_cnt = serializers.IntegerField()
    saved_notes_cnt = serializers.IntegerField()
    saved_beans_cnt = serializers.IntegerField()


class PrefCalendarSerializer(serializers.Serializer):
    created_date = serializers.DateField(format="%Y-%m-%d")


class PrefTastedRecordSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="bean.name")
    star = serializers.FloatField(source="taste_review.star")
    flavor = serializers.CharField(source="taste_review.flavor")
    first_photo = serializers.SerializerMethodField()
    created_date = serializers.DateField()

    class Meta:
        model = TastedRecord
        fields = ["id", "title", "star", "flavor", "first_photo", "created_date"]

    def get_first_photo(self, obj):
        first_photo = Photo.objects.filter(tasted_record=obj).order_by("created_at").first()
        return first_photo.photo_url.url if first_photo and first_photo.photo_url else None


class PrefPostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.nickname")
    first_photo = serializers.SerializerMethodField()
    created_date = serializers.DateField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ["id", "title", "subject", "author", "first_photo", "created_date", "created_at"]

    def get_first_photo(self, obj):
        first_photo = Photo.objects.filter(post=obj).order_by("created_at").first()
        return first_photo.photo_url.url if first_photo and first_photo.photo_url else None

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)


class PrefSavedBeanSerializer(serializers.ModelSerializer):
    avg_star = serializers.FloatField()
    image_url = serializers.URLField()
    created_date = serializers.DateField()

    class Meta:
        model = Bean
        fields = ["id", "name", "bean_type", "roast_point", "avg_star", "image_url", "created_date"]


class PrefStarSerializer(serializers.Serializer):
    star_distribution = serializers.DictField(child=serializers.IntegerField(), help_text="각 별점별 개수")
    most_common_star = serializers.FloatField(help_text="가장 개수가 많은 별점", allow_null=True)
    avg_star = serializers.FloatField(help_text="별점 평균 (소수점 첫째 자리까지)")
    total_ratings = serializers.IntegerField(help_text="총 별점 개수")


class PrefFlavorSerializer(serializers.Serializer):
    top_flavors = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField(), allow_empty=True), help_text="유저가 가장 선호하는 맛 TOP 5"
    )


class PrefCountrySerializer(serializers.Serializer):
    top_origins = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()), help_text="유저가 가장 선호하는 원산지 TOP 5"
    )
