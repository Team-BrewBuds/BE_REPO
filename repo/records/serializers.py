from rest_framework import serializers

from repo.common.utils import get_time_difference
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Comment, Note, Post, Report, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.services import get_post_or_tasted_record_or_comment
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
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.select_related("author").filter(parent__isnull=True), required=False
    )
    author = UserSimpleSerializer(read_only=True)
    like_cnt = serializers.IntegerField(source="like_cnt.count", read_only=True)
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
            return CommentSerializer(obj.replies_list, many=True).data

        return []

    class Meta:
        model = Comment
        fields = ["id", "content", "parent", "author", "like_cnt", "created_at", "replies", "is_user_liked"]


class ReportSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    target_author = serializers.CharField(read_only=True)

    def validate(self, data):
        required_fields = ["object_type", "object_id", "reason"]
        for field in required_fields:
            if field not in data:
                raise serializers.ValidationError(f"{field}는 필수 항목입니다.")

        valid_object_types = ["post", "tasted_record", "comment"]
        if data["object_type"] not in valid_object_types:
            raise serializers.ValidationError("유효하지 않은 신고 대상 타입입니다.")

        target_object = get_post_or_tasted_record_or_comment(data["object_type"], data["object_id"])
        if target_object.author == self.context["request"].user:
            raise serializers.ValidationError("자기 자신의 컨텐츠는 신고할 수 없습니다.")

        return data

    class Meta:
        model = Report
        fields = ["author", "target_author", "object_type", "object_id", "reason"]
