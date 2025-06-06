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
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        if obj.post and hasattr(obj.post, "post_photos"):
            photos = obj.post.post_photos
            return photos[0].photo_url.url if photos else None
        return None

    def get_created_at(self, obj):
        return get_time_difference(obj.post.created_at)

    class Meta:
        model = Note
        fields = ["post_id", "title", "subject", "created_at", "nickname", "photo_url"]


class NoteTastedRecordSimpleSerializer(serializers.ModelSerializer):
    tasted_record_id = serializers.IntegerField(source="tasted_record.id")
    bean_name = serializers.CharField(source="tasted_record.bean.name")
    flavor = serializers.CharField(source="tasted_record.taste_review.flavor")
    photo_url = serializers.SerializerMethodField()
    star = serializers.FloatField(source="tasted_record.taste_review.star", read_only=True, default=0, min_value=0, max_value=5)

    def get_photo_url(self, obj):
        if obj.tasted_record and hasattr(obj.tasted_record, "tasted_record_photos"):
            photos = obj.tasted_record.tasted_record_photos
            return photos[0].photo_url.url if photos else None
        return None

    class Meta:
        model = Note
        fields = ["tasted_record_id", "bean_name", "flavor", "photo_url", "star"]
