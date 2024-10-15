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
    parent = serializers.PrimaryKeyRelatedField(queryset=Comment.objects.all(), required=False)
    author = UserSimpleSerializer(read_only=True)
    like_cnt = serializers.IntegerField(source="like_cnt.count", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    replies = serializers.SerializerMethodField()
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        request = self.context.get("request")
        if request:
            user = request.user
            return obj.like_cnt.filter(id=user.id).exists()
        return False

    def get_replies(self, obj):
        if hasattr(obj, "replies_list"):
            return CommentSerializer(obj.replies_list, many=True).data

        return []

    class Meta:
        model = Comment
        fields = ["id", "content", "parent", "author", "like_cnt", "created_at", "replies", "is_user_liked"]

class LikeSerializer(serializers.Serializer):
    object_type = serializers.ChoiceField(choices=["post", "tasted_record", "comment"])
    object_id = serializers.IntegerField()

class NoteSerializer(serializers.ModelSerializer):
    object_type = serializers.ChoiceField(choices=["post", "tasted_record"])
    object_id = serializers.IntegerField()

    class Meta:
        model = Note
        fields = ["object_type", "object_id"]
