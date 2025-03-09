from rest_framework import serializers

from repo.common.serializers import PhotoSerializer
from repo.common.utils import get_time_difference
from repo.interactions.serializers import InteractionMethodSerializer
from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Photo, Post, TastedRecord
from repo.records.tasted_record.serializers import TastedRecordInPostSerializer


class PostListSerializer(serializers.ModelSerializer):
    """게시글 리스트 조회용"""

    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set", read_only=True)
    tasted_records = TastedRecordInPostSerializer("tasted_records", many=True, read_only=True)
    created_at = serializers.SerializerMethodField()
    subject = serializers.CharField(source="get_subject_display")
    likes = serializers.IntegerField()
    comments = serializers.IntegerField(source="comment_set.count")
    is_user_liked = serializers.BooleanField(default=False, read_only=True)
    is_user_noted = serializers.BooleanField(default=False, read_only=True)
    is_user_following = serializers.BooleanField(default=False, read_only=True)

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = Post
        exclude = ["like_cnt"]


class TopPostSerializer(PostListSerializer):
    """인기 게시글 리스트 조회용"""

    def get_fields(self):
        fields = super().get_fields()
        for field in ["is_user_noted", "tasted_records"]:
            fields.pop(field, None)
        return fields


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """게시글 생성, 수정용"""

    tasted_records = serializers.PrimaryKeyRelatedField(many=True, queryset=TastedRecord.objects.all(), required=False)
    photos = serializers.PrimaryKeyRelatedField(many=True, queryset=Photo.objects.all(), required=False)

    class Meta:
        model = Post
        fields = ["title", "content", "subject", "tag", "tasted_records", "photos"]


class PostDetailSerializer(serializers.ModelSerializer):
    """단일 게시글 조회용"""

    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    tasted_records = TastedRecordInPostSerializer("post.tasted_records", many=True)
    subject = serializers.CharField(source="get_subject_display")
    created_at = serializers.SerializerMethodField()
    interaction = serializers.SerializerMethodField()

    def get_interaction(self, obj):
        context = {"request": self.context.get("request")}
        return InteractionMethodSerializer(obj, context=context).data

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = Post
        exclude = ["like_cnt"]


class UserPostSerializer(serializers.ModelSerializer):
    """특정 사용자의 게시글 리스트 조회용"""

    author = serializers.CharField(source="author.nickname", read_only=True)
    subject = serializers.CharField(source="get_subject_display")
    represent_post_photo = serializers.SerializerMethodField()
    tasted_records_photo = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_represent_post_photo(self, obj):
        """게시글의 첫번째 사진 URL 반환"""
        if photos := obj.photo_set.all():
            return photos[0].photo_url.url
        return None

    def get_tasted_records_photo(self, obj):
        """게시글에 연결된 시음기록의 첫번째 사진 URL 반환"""
        if not (tasted_records := obj.tasted_records.all()):
            return None

        if photos := tasted_records[0].photo_set.all():
            return photos[0].photo_url.url
        return None

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = Post
        fields = ["id", "author", "title", "subject", "created_at", "represent_post_photo", "tasted_records_photo"]
