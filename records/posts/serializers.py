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
        fields = "__all__" 


class PostDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.user_id')
    user_nickname = serializers.CharField(source='user.nickname')
    user_profile_image = serializers.URLField(source='user.profile_image')
    photos = PhotoSerializer(many=True, source='photo_set')
    like_cnt = serializers.IntegerField(source="like_cnt.count")

    tasted_record = TastedRecordFeedSerializer('tasted_record', read_only=True)

    class Meta:
        model = Post
        fields = "__all__"
