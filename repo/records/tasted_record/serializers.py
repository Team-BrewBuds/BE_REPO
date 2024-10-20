from rest_framework import serializers

from repo.beans.serializers import BeanSerializer, BeanTasteReviewSerializer
from repo.common.serializers import PhotoSerializer
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Photo, TastedRecord


class TastedRecordListSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    bean_name = serializers.CharField(source="bean.name")
    bean_type = serializers.CharField(source="bean.get_bean_type_display")
    star_rating = serializers.IntegerField(source="taste_review.star")
    flavor = serializers.CharField(source="taste_review.flavor")
    photos = PhotoSerializer(many=True, source="photo_set", read_only=True)
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.like_cnt.filter(id=user.id).exists()
        return False

    class Meta:
        model = TastedRecord
        fields = [
            "id",
            "author",
            "bean_name",
            "bean_type",
            "star_rating",
            "flavor",
            "content",
            "view_cnt",
            "like_cnt",
            "is_private",
            "created_at",
            "tag",
            "photos",
            "is_user_liked",
        ]


class TastedRecordDetailSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    bean = BeanSerializer("bean")
    taste_review = BeanTasteReviewSerializer("taste_review")

    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return obj.like_cnt.filter(id=user.id).exists()
        return False

    class Meta:
        model = TastedRecord
        fields = "__all__"


class TastedRecordCreateUpdateSerializer(serializers.ModelSerializer):
    bean = BeanSerializer("bean")
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
