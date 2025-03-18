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
    avg_star = serializers.FloatField(read_only=True)
    record_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Bean
        fields = [
            "id",
            "name",
            "bean_type",
            "is_official",
            "is_decaf",
            "origin_country",
            "image_url",
            "avg_star",
            "record_count",
        ]


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
    photo_url = serializers.URLField(read_only=True)
    author = serializers.CharField(source="author.nickname", read_only=True)
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "title",
            "content",
            "photo_url",
            "likes",
            "comment_count",
            "subject",
            "created_at",
            "view_cnt",
            "author",
        ]


class BaseQuerySerializer(serializers.Serializer):
    """기본 추천 검색어 시리얼라이저"""

    q = serializers.CharField(required=True, allow_blank=False)


class BaseSuggestInputSerializer(BaseQuerySerializer):
    """검색어 추천 기본 시리얼라이저"""

    pass


class BuddySuggestInputSerializer(BaseSuggestInputSerializer):
    """사용자 검색어 추천 시리얼라이저"""

    pass


class BeanSuggestInputSerializer(BaseSuggestInputSerializer):
    """원두 검색어 추천 시리얼라이저"""

    pass


class TastedRecordSuggestInputSerializer(BaseSuggestInputSerializer):
    """시음기록 검색어 추천 시리얼라이저"""

    pass


class PostSuggestInputSerializer(BaseSuggestInputSerializer):
    """게시글 검색어 추천 시리얼라이저"""

    pass


class SuggestSerializer(serializers.Serializer):
    """검색어 추천 시리얼라이저"""

    suggestions = serializers.ListField(child=serializers.CharField(), required=True)


class BaseSearchInputSerializer(serializers.Serializer):
    """검색 기본 시리얼라이저"""

    q = serializers.CharField(required=True, allow_blank=False)


class BuddySearchInputSerializer(BaseSearchInputSerializer):
    """사용자 검색 시리얼라이저"""

    SORT_CHOICES = [("record_cnt", "기록 수"), ("follower_cnt", "팔로워 수")]
    sort_by = serializers.ChoiceField(choices=SORT_CHOICES, required=False)


class BeanQueryFilterSerializer(serializers.Serializer):
    """원두 필터링 시리얼라이저"""

    bean_type = serializers.ChoiceField(choices=Bean.bean_type_choices, required=False)
    origin_country = serializers.CharField(required=False)
    min_star = serializers.FloatField(required=False, min_value=0, max_value=5)
    max_star = serializers.FloatField(required=False, min_value=0, max_value=5)
    is_decaf = serializers.BooleanField(required=False)


class BeanSearchInputSerializer(BaseSearchInputSerializer, BeanQueryFilterSerializer):
    """원두 검색 시리얼라이저"""

    SORT_CHOICES = [("record_count", "기록 수"), ("avg_star", "평균 별점")]
    sort_by = serializers.ChoiceField(choices=SORT_CHOICES, required=False)


class TastedRecordSearchInputSerializer(BaseSearchInputSerializer, BeanQueryFilterSerializer):
    """시음기록 검색 시리얼라이저"""

    SORT_CHOICES = [("star_rank", "별점순"), ("latest", "최신순"), ("like_rank", "좋아요순")]
    sort_by = serializers.ChoiceField(choices=SORT_CHOICES, required=False)


class PostSearchInputSerializer(BaseSearchInputSerializer):
    """게시글 검색 시리얼라이저"""

    SORT_CHOICES = [("latest", "최신순"), ("like_rank", "좋아요순")]
    subject = serializers.ChoiceField(choices=Post.SUBJECT_TYPE_CHOICES, required=False)
    sort_by = serializers.ChoiceField(choices=SORT_CHOICES, required=False)
