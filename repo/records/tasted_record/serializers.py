from rest_framework import serializers

from repo.beans.serializers import BeanSerializer, BeanTasteReviewSerializer
from repo.common.serializers import PhotoSerializer
from repo.common.utils import get_first_photo_url, get_time_difference
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Photo, TastedRecord


class TastedRecordListSerializer(serializers.ModelSerializer):
    """시음 기록 리스트 조회용"""

    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set", read_only=True)
    # 원두 정보
    bean_name = serializers.CharField(source="bean.name")
    bean_type = serializers.CharField(source="bean.get_bean_type_display")
    star_rating = serializers.IntegerField(source="taste_review.star")
    flavor = serializers.CharField(source="taste_review.flavor")
    # 기타 정보
    created_at = serializers.SerializerMethodField()
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    is_user_liked = serializers.BooleanField(default=False, read_only=True)
    is_user_noted = serializers.BooleanField(default=False, read_only=True)
    is_user_following = serializers.BooleanField(default=False, read_only=True)

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = TastedRecord
        exclude = ["like_cnt", "bean", "taste_review"]


class TastedRecordDetailSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    bean = BeanSerializer("bean")
    taste_review = BeanTasteReviewSerializer("taste_review")

    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.like_cnt.filter(id=user.id).exists()
        return False

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = TastedRecord
        fields = "__all__"


class TastedRecordCreateUpdateSerializer(serializers.ModelSerializer):
    bean = BeanSerializer("bean", required=False)
    taste_review = BeanTasteReviewSerializer("taste_review")
    photos = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Photo.objects.all(),
        required=False,
    )

    class Meta:
        model = TastedRecord
        fields = ["content", "is_private", "tag", "bean", "taste_review", "photos"]


class TastedRecordInPostSerializer(serializers.ModelSerializer):
    bean_name = serializers.CharField(source="bean.name")
    bean_type = serializers.CharField(source="bean.get_bean_type_display")
    star_rating = serializers.IntegerField(source="taste_review.star")
    flavor = serializers.CharField(source="taste_review.flavor")
    photos = PhotoSerializer(many=True, source="photo_set")

    class Meta:
        model = TastedRecord
        fields = ["id", "content", "bean_name", "bean_type", "star_rating", "flavor", "photos"]


class UserTastedRecordSerializer(serializers.ModelSerializer):
    bean_name = serializers.CharField(source="bean.name")
    star = serializers.FloatField(source="taste_review.star")
    photo_url = serializers.SerializerMethodField()
    likes = serializers.IntegerField()

    def get_photo_url(self, obj):
        return get_first_photo_url(obj)

    class Meta:
        model = TastedRecord
        fields = ["id", "bean_name", "star", "photo_url", "likes"]
