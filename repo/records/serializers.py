from rest_framework import serializers

from repo.common.utils import get_time_difference
from repo.interactions.note.models import Note
from repo.records.models import Post, TastedRecord
from repo.records.posts.serializers import PostListSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer


class FeedSerializer(serializers.Serializer):
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
    created_at = serializers.SerializerMethodField()
    nickname = serializers.CharField(source="post.author.nickname", read_only=True)
    photo_url = serializers.CharField(read_only=True)

    def get_created_at(self, obj):
        return get_time_difference(obj.post.created_at)

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
