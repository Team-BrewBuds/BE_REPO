from rest_framework import serializers

from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Comment, Note, Post, TastedRecord


class FeedSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        if isinstance(instance, Post):
            return PostListSerializer(instance).data
        elif isinstance(instance, TastedRecord):
            return TastedRecordListSerializer(instance).data
        return super().to_representation(instance)


class CommentSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=200)
    author = UserSimpleSerializer(read_only=True)
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    created_at = serializers.DateTimeField(read_only=True)
    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        if hasattr(obj, "replies_list"):
            return CommentSerializer(obj.replies_list, many=True).data

        return []

    class Meta:
        model = Comment
        fields = ["id", "content", "author", "like_cnt", "created_at", "replies"]


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = "__all__"
