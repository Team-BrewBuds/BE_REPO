from rest_framework import serializers
from records.models import Post
from records.serializers import PhotoSerializer
from records.tasted_record.serializers import TastedRecordFeedSerializer

class PostFeedSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.user_id')
    user_nickname = serializers.CharField(source='user.nickname')
    user_profile_image = serializers.URLField(source='user.profile_image')
    photos = PhotoSerializer(many=True, source='photo_set')

    tasted_record = TastedRecordFeedSerializer('tasted_record', read_only=True)

    class Meta:
        model = Post
        fields = (
            'post_id', 'title', 'content', 'subject', 'view_cnt', 'like_cnt', 'created_at',
            'user_id', 'user_nickname', 'user_profile_image', 'photos',
            'tasted_record'
        )
