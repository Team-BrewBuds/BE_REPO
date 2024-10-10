from rest_framework import serializers

from repo.profiles.serializers import UserSimpleSerializer
from repo.records.models import Post
from repo.records.serializers import PhotoSerializer
from repo.records.tasted_record.serializers import TastedRecordFeedSerializer


class PostFeedSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    tasted_record = TastedRecordFeedSerializer("tasted_record", read_only=True)
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)

    class Meta:
        model = Post
        fields = "__all__"


class PostDetailSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    tasted_record = TastedRecordFeedSerializer("tasted_record", read_only=True)

    like_cnt = serializers.IntegerField(source="like_cnt.count")
    is_user_liked = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)

    class Meta:
        model = Post
        fields = "__all__"


class TopPostSerializer(serializers.ModelSerializer):
    author = UserSimpleSerializer(read_only=True)
    photos = PhotoSerializer(many=True, source="photo_set")
    is_user_liked = serializers.SerializerMethodField()
    like_cnt = serializers.IntegerField(source="like_cnt.count")
    comment_cnt = serializers.SerializerMethodField()

    def get_is_user_liked(self, obj):
        return obj.is_user_liked(obj.author)

    def get_comment_cnt(self, obj):
        return obj.comment_cnt()

    class Meta:
        model = Post
        fields = "__all__"
