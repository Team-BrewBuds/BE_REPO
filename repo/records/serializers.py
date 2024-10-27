from rest_framework import serializers

from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Comment, Note, Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer


class FeedSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        if isinstance(instance, Post):
            return PostListSerializer(instance).data
        elif isinstance(instance, TastedRecord):
            return TastedRecordListSerializer(instance).data
        return super().to_representation(instance)


class UserNoteSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, Note):
            if instance.post:
                return NotePostSimpleSerializer(instance).data
            elif instance.tasted_record:
                return NoteTastedRecordSimpleSerializer(instance).data
        return super().to_representation(instance)


class NotePostSimpleSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(source="post.id")
    title = serializers.CharField(source="post.title")
    subject = serializers.CharField(source="post.subject")
    created_at = serializers.DateTimeField(source="post.created_at")
    nickname = serializers.CharField(source="post.author.nickname", read_only=True)
    photo_url = serializers.CharField(read_only=True)

    class Meta:
        model = Note
        fields = ["post_id", "title", "subject", "created_at", "nickname", "photo_url"]


class NoteTastedRecordSimpleSerializer(serializers.ModelSerializer):
    tasted_record_id = serializers.IntegerField(source="tasted_record.id")
    bean_name = serializers.CharField(source="tasted_record.bean.name")
    flavor = serializers.CharField(source="tasted_record.taste_review.flavor")
    photo_url = serializers.CharField(read_only=True)

    class Meta:
        model = Note
        fields = ["tasted_record_id", "bean_name", "flavor", "photo_url"]


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
