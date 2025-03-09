from django.db.models import Q
from rest_framework import serializers

from repo.interactions.note.models import Note
from repo.interactions.relationship.models import Relationship
from repo.records.models import Post, TastedRecord


class InteractionSerializer(serializers.Serializer):
    is_user_liked = serializers.BooleanField(default=False, read_only=True)
    is_user_noted = serializers.BooleanField(default=False, read_only=True)
    is_user_following = serializers.BooleanField(default=False, read_only=True)


class InteractionMethodSerializer(serializers.Serializer):
    is_user_liked = serializers.SerializerMethodField(default=False, read_only=True)
    is_user_noted = serializers.SerializerMethodField(default=False, read_only=True)
    is_user_following = serializers.SerializerMethodField(default=False, read_only=True)

    def get_is_user_liked(self, obj: Post | TastedRecord) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return obj.like_cnt.filter(id=request.user.id).exists()

    def get_is_user_noted(self, obj: Post | TastedRecord) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        filters = Q(post=obj) if isinstance(obj, Post) else Q(tasted_record=obj)
        return Note.objects.filter(filters, author=request.user).exists()

    def get_is_user_following(self, obj: Post | TastedRecord) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return Relationship.objects.filter(from_user=request.user, to_user=obj.author, relationship_type="follow").exists()
