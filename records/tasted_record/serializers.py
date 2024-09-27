from rest_framework import serializers
from records.models import Tasted_Record, Photo
from beans.serializers import BeanSerializer, BeanTasteAndReviewSerializer

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['photo_url']


class TastedRecordSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, source='photo_set')
    user_id = serializers.IntegerField(source='user.user_id')
    user_nickname = serializers.CharField(source='user.nickname')
    user_profile_image = serializers.URLField(source='user.profile_image')
    like_cnt = serializers.IntegerField(source='like_cnt.count')
    bean_name = serializers.CharField(source='bean.name')
    bean_type = serializers.CharField(source='bean.get_bean_type_display')
    star_rating = serializers.IntegerField(source='taste_and_review.star')
    flavor = serializers.CharField(source='taste_and_review.flavor')

    class Meta:
        model = Tasted_Record
        fields = (
            'tasted_record_id', 'content', 'view_cnt', 'like_cnt', 'created_at',
            'photos', 'user_id', 'user_nickname', 'user_profile_image', 'bean_name',
            'bean_type', 'star_rating', 'flavor'
        )
    
class TastedRecordDetailSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, source='photo_set')
    user_id = serializers.IntegerField(source='user.user_id')
    user_nickname = serializers.CharField(source='user.nickname')
    user_profile_image = serializers.URLField(source='user.profile_image')
    like_cnt = serializers.IntegerField(source='like_cnt.count')

    bean = BeanSerializer('bean')
    taste_and_review = BeanTasteAndReviewSerializer('taste_and_review')

    class Meta:
        model = Tasted_Record
        fields = (
            'tasted_record_id', 'content', 'view_cnt', 'like_cnt', 'created_at',
            'photos', 'user_id', 'user_nickname', 'user_profile_image',
            'bean', 'taste_and_review'
        )

class PageNumberSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)

    def validate_page(self, value):
        if value < 1:
            raise serializers.ValidationError("Page number must be a positive integer.")
        return value