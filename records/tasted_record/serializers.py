from rest_framework import serializers

from beans.serializers import BeanSerializer, BeanTasteAndReviewSerializer
from records.models import Tasted_Record
from records.serializers import PhotoSerializer
from profiles.serializers import UserSimpleSerializer


class TastedRecordFeedSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")

    bean_name = serializers.CharField(source="bean.name")
    bean_type = serializers.CharField(source="bean.get_bean_type_display")
    star_rating = serializers.IntegerField(source="taste_and_review.star")
    flavor = serializers.CharField(source="taste_and_review.flavor")
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.user)

    class Meta:
        model = Tasted_Record
        fields = "__all__" 


class TastedRecordDetailSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    bean = BeanSerializer("bean")
    taste_and_review = BeanTasteAndReviewSerializer("taste_and_review")

    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.user)
    
    class Meta:
        model = Tasted_Record
        fields = "__all__" 
