from rest_framework import serializers
from records.models import Tasted_Record, Photo


class TastedRecordListSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField(source='user.user_id')
    user_nickname = serializers.ReadOnlyField(source='user.nickname')
    user_profile_image = serializers.ReadOnlyField(source='user.profile_image')
    bean_name = serializers.ReadOnlyField(source='bean.name')
    bean_type = serializers.ReadOnlyField(source='bean.bean_type')
    star = serializers.ReadOnlyField(source='taste_and_review.star')
    flavor = serializers.ReadOnlyField(source='taste_and_review.flavor')
    tasted_record_image = serializers.SerializerMethodField()

    def get_tasted_record_image(self, obj):
        photo = Photo.objects.filter(tasted_record=obj)
        print(photo)
        if photo.exists():
            return [p for p in photo.values_list('photo_url', flat=True)]
        return None

    class Meta:
        model = Tasted_Record
        fields = (
            'tasted_record_id', 'content', 'view_cnt', 'like_cnt', 'created_at',
            'user_id', 'user_nickname', 'user_profile_image',
            'bean_name', 'bean_type', 'star', 'flavor',
            'tasted_record_image'
        )
