from rest_framework import serializers

from repo.beans.serializers import BeanSerializer, BeanTasteAndReviewSerializer
from repo.records.models import TastedRecord
from repo.records.serializers import PhotoSerializer
from repo.profiles.serializers import UserSimpleSerializer


class TastedRecordFeedSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")

    bean_name = serializers.CharField(source="bean.name")
    bean_type = serializers.CharField(source="bean.get_bean_type_display")
    star_rating = serializers.IntegerField(source="taste_review.star")
    flavor = serializers.CharField(source="taste_review.flavor")
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)

    class Meta:
        model = TastedRecord
        fields = "__all__" 


class TastedRecordDetailSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    bean = BeanSerializer("bean")
    taste_review = BeanTasteAndReviewSerializer("taste_review")

    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)
    
    class Meta:
        model = TastedRecord
        fields = "__all__" 
