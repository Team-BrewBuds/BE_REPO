from rest_framework import serializers

from repo.beans.serializers import BeanSerializer, BeanTasteReviewSerializer
from repo.common.serializers import PhotoSerializer
from repo.common.utils import get_time_difference
from repo.interactions.serializers import (
    InteractionMethodSerializer,
    InteractionSerializer,
)
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Photo, TastedRecord


class TastedRecordListSerializer(serializers.ModelSerializer):
    """시음 기록 리스트 조회용"""

    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set", read_only=True)
    # 원두 정보
    bean_name = serializers.CharField(source="bean.name")
    bean_type = serializers.CharField(source="bean.get_bean_type_display")
    star_rating = serializers.FloatField(source="taste_review.star")
    flavor = serializers.CharField(source="taste_review.flavor")
    # 기타 정보
    created_at = serializers.SerializerMethodField()
    likes = serializers.IntegerField()
    comments = serializers.IntegerField(source="comment_set.count")
    interaction = serializers.SerializerMethodField(read_only=True)

    def get_interaction(self, obj):
        context = {"request": self.context.get("request")}
        return InteractionSerializer(obj, context=context).data

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
    likes = serializers.IntegerField()
    created_at = serializers.SerializerMethodField()
    interaction = serializers.SerializerMethodField(read_only=True)

    def get_interaction(self, obj):
        context = {"request": self.context.get("request")}
        return InteractionMethodSerializer(obj, context=context).data

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = TastedRecord
        exclude = ["like_cnt"]


class TastedRecordCreateUpdateSerializer(serializers.ModelSerializer):
    bean = BeanSerializer("bean", required=False)  # 수정시 원두 데이터 필수 입력 아님
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
    star_rating = serializers.FloatField(source="taste_review.star")
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
        if obj.tasted_record_photos:
            return obj.tasted_record_photos[0].photo_url.url
        return None

    class Meta:
        model = TastedRecord
        fields = ["id", "bean_name", "star", "photo_url", "likes"]
