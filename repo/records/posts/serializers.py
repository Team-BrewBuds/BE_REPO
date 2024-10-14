from rest_framework import serializers

from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Post, TastedRecord
from repo.records.serializers import PhotoSerializer
from repo.records.tasted_record.serializers import TastedRecordListSerializer,TastedRecordInPostSerializer


class PostListSerializer(serializers.ModelSerializer):
    """ 게시글 리스트 조회용"""
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    tasted_record = TastedRecordListSerializer("tasted_record", read_only=True)
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)

    class Meta:
        model = Post
        fields = "__all__"

class TopPostSerializer(PostListSerializer):
    """인기 게시글 리스트 조회용"""
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    comment_cnt = serializers.SerializerMethodField()

    def get_comment_cnt(self, obj):
        return obj.comment_cnt()

    class Meta:
        model = Post
        fields = ["id", "author", "title", "content", "subject", "tag", "photos", "like_cnt", "comment_cnt", "is_user_liked"]

class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """ 게시글 생성, 수정용"""
    tasted_record = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=TastedRecord.objects.all()),
        required=False
    )
    photos = PhotoSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ["author", "title", "content", "subject", "tag", "tasted_record", "photos"]

class PostDetailSerializer(serializers.ModelSerializer):
    """ 단일 게시글 조회용"""
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    tasted_records = TastedRecordInPostSerializer("post.tasted_records", many=True)

    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)

    class Meta:
        model = Post
        fields = "__all__"

class PostUpdateSerializer(serializers.ModelSerializer):
    """ 게시글 수정용"""
    photos = PhotoSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ["title", "content", "subject", "tag", "tasted_records", "photos"]
