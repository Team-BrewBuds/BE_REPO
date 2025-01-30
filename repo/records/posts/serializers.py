from rest_framework import serializers

from repo.common.serializers import PhotoSerializer
from repo.common.utils import get_time_difference
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
    likes = serializers.IntegerField(source="like_cnt.count")
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
        for field in ["is_user_noted", "like_cnt", "tasted_records"]:
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
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.like_cnt.filter(id=request.user.id).exists()
        return False

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = Post
        fields = "__all__"


class UserPostSerializer(serializers.ModelSerializer):
    """특정 사용자의 게시글 리스트 조회용"""

    author = serializers.CharField(source="author.nickname", read_only=True)
    subject = serializers.CharField(source="get_subject_display")
    represent_post_photo = serializers.SerializerMethodField()
    tasted_records_photo = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_represent_post_photo(self, obj):
        photos = obj.photo_set.all()
        if photos.exists():
            return PhotoSerializer(photos.first()).data
        return None

    def get_tasted_records_photo(self, obj):
        for tasted_record in obj.tasted_records.all():
            if tasted_record.photo_set.exists():
                return PhotoSerializer(tasted_record.photo_set.first()).data
        return None

    def get_created_at(self, obj):
        return get_time_difference(obj.created_at)

    class Meta:
        model = Post
        fields = ["id", "author", "title", "subject", "created_at", "represent_post_photo", "tasted_records_photo"]
