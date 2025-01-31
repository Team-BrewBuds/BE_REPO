from rest_framework import serializers

from repo.common.utils import get_time_difference
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Comment


class CommentInputSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=200)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.select_related("author").filter(parent__isnull=True), required=False
    )


class CommentOutputSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=200)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.select_related("author").filter(parent__isnull=True), required=False
    )
    author = UserSimpleSerializer(read_only=True)
    likes = serializers.IntegerField(read_only=True)
    created_at = serializers.SerializerMethodField(read_only=True)
    replies = serializers.SerializerMethodField()
    is_user_liked = serializers.SerializerMethodField()

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    def get_is_user_liked(self, obj):
        request = self.context.get("request")
        if request:
            user = request.user
            return obj.like_cnt.filter(id=user.id).exists()
        return False

    def get_replies(self, obj):
        if hasattr(obj, "replies_list"):
            return CommentOutputSerializer(obj.replies_list, many=True).data

        return []

    class Meta:
        model = Comment
        fields = ["id", "content", "parent", "author", "likes", "created_at", "replies", "is_user_liked"]
