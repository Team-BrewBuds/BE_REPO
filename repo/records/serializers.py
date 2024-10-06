import importlib
from rest_framework import serializers

from repo.records.models import Post, TastedRecord, Photo, Comment, Note
from repo.profiles.serializers import UserSimpleSerializer


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
    
class FeedSerializer(serializers.ModelSerializer):
    
    def to_representation(self, instance):
        # 순환 참조 피하기 위함
        post_serializer_module = importlib.import_module('repo.records.posts.serializers')
        tasted_record_serializer_module = importlib.import_module('repo.records.tasted_record.serializers')
        PostFeedSerializer = getattr(post_serializer_module, 'PostFeedSerializer')
        TastedRecordFeedSerializer = getattr(tasted_record_serializer_module, 'TastedRecordFeedSerializer')

        if isinstance(instance, Post):
            return PostFeedSerializer(instance).data
        elif isinstance(instance, TastedRecord):
            return TastedRecordFeedSerializer(instance).data
        return super().to_representation(instance)

class CommentSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=200)
    author = UserSimpleSerializer(read_only=True)
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    created_at = serializers.DateTimeField(read_only=True)
    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        if hasattr(obj, 'replies_list'):
            return CommentSerializer(obj.replies_list, many=True).data
        
        return []

    class Meta:
        model = Comment
        fields = ["id", "content", "author", "like_cnt", "created_at", "replies"]

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = "__all__"
