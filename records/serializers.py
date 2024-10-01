from rest_framework import serializers

from records.models import Photo, Comment
from profiles.serializers import UserSimpleSerializer


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["photo_url"]


class PageNumberSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)

    def validate_page(self, value):
        if value < 1:
            raise serializers.ValidationError("Page number must be a positive integer.")
        return value

class CommentSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=200)
    user = UserSimpleSerializer(read_only=True)
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    created_at = serializers.DateTimeField(read_only=True)
    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        if hasattr(obj, 'replies_list'):
            return CommentSerializer(obj.replies_list, many=True).data
        
        return []

    class Meta:
        model = Comment
        fields = ["comment_id", "content", "user", "like_cnt", "created_at", "replies"]
