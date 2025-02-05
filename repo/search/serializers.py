from rest_framework import serializers

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.records.models import Photo, Post, TastedRecord


class BuddySearchSerializer(serializers.ModelSerializer):
    record_cnt = serializers.IntegerField()
    follower_cnt = serializers.IntegerField()

    class Meta:
        model = CustomUser
        fields = ["id", "nickname", "email", "profile_image", "record_cnt", "follower_cnt"]


class BeanSearchSerializer(serializers.ModelSerializer):
    avg_star = serializers.SerializerMethodField()
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = Bean
        fields = [
            "id",
            "name",
            "bean_type",
            "is_decaf",
            "origin_country",
            "image_url",
            "avg_star",
            "record_count",
        ]

    def get_avg_star(self, obj):
        stats_dict = self.context.get("stats_dict", {})
        avg_star = stats_dict.get(obj.id, {}).get("avg_star", 0)
        return round(avg_star, 1) if avg_star else 0

    def get_record_count(self, obj):
        stats_dict = self.context.get("stats_dict", {})
        return stats_dict.get(obj.id, {}).get("record_count", 0)


class TastedRecordSearchSerializer(serializers.ModelSerializer):
    bean_name = serializers.CharField(source="bean.name", read_only=True)  # 원두명
    author_nickname = serializers.CharField(source="author.nickname", read_only=True)
    star = serializers.FloatField(source="taste_review.star", read_only=True)
    bean_type = serializers.CharField(source="bean.bean_type", read_only=True)  # 원두 유형
    bean_taste = serializers.CharField(source="taste_review.flavor", read_only=True)  # 원두 맛
    photo_url = serializers.SerializerMethodField()  # 사진 URL

    class Meta:
        model = TastedRecord
        fields = ["id", "author_nickname", "content", "bean_name", "star", "bean_type", "bean_taste", "photo_url"]

    def get_photo_url(self, obj):
        photo = Photo.objects.filter(tasted_record=obj).first()
        return photo.photo_url.url if photo and photo.photo_url else None


class PostSearchSerializer(serializers.ModelSerializer):
    photos = serializers.SerializerMethodField()
    like_cnt = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    author = serializers.CharField(source="author.nickname", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "photos",
            "like_cnt",
            "comment_count",
            "subject",
            "created_at",
            "view_cnt",
            "author",
        ]

    def get_photos(self, obj):
        photo = Photo.objects.filter(post=obj).first()
        return photo.photo_url.url if photo and photo.photo_url else None

    def get_like_cnt(self, obj):
        return obj.like_cnt.count()

    def get_comment_count(self, obj):
        return obj.comment_cnt()
