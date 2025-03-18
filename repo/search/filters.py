from django.db.models import Q
from django_filters import (
    BooleanFilter,
    CharFilter,
    ChoiceFilter,
    FilterSet,
    NumberFilter,
)

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


class BuddyFilter(FilterSet):
    """
    사용자 검색 필터
    """

    SORT_CHOICES = [
        ("record_cnt", "기록 수"),
        ("follower_cnt", "팔로워 수"),
    ]

    q = CharFilter(field_name="nickname", lookup_expr="icontains")
    sort_by = ChoiceFilter(choices=SORT_CHOICES, method="filter_sort_by")

    def filter_sort_by(self, queryset, name, value):
        if value == "record_cnt":
            return queryset.order_by("-record_cnt")
        elif value == "follower_cnt":
            return queryset.order_by("-follower_cnt")
        return queryset

    class Meta:
        model = CustomUser
        fields = ["q", "sort_by"]


class BeanFilter(FilterSet):
    """
    원두 검색 필터
    """

    SORT_CHOICES = [
        ("avg_star", "평균 별점"),
        ("record_count", "기록 수"),
    ]

    q = CharFilter(field_name="name", lookup_expr="icontains")
    bean_type = CharFilter(field_name="bean_type")
    origin_country = CharFilter(field_name="origin_country")
    is_decaf = BooleanFilter(field_name="is_decaf")
    min_star = NumberFilter(field_name="avg_star", lookup_expr="gte")
    max_star = NumberFilter(field_name="avg_star", lookup_expr="lte")
    sort_by = ChoiceFilter(choices=SORT_CHOICES, method="filter_sort_by")

    def filter_sort_by(self, queryset, name, value):
        if value == "avg_star":
            return queryset.order_by("-avg_star")
        elif value == "record_count":
            return queryset.order_by("-record_count")
        return queryset

    class Meta:
        model = Bean
        fields = ["q", "bean_type", "origin_country", "is_decaf", "min_star", "max_star", "sort_by"]


class TastedRecordFilter(FilterSet):
    """
    시음기록 검색 필터
    """

    SORT_CHOICES = [
        ("latest", "최신순"),
        ("like_rank", "좋아요순"),
        ("star_rank", "별점순"),
    ]
    q = CharFilter(method="filter_query")
    bean_type = CharFilter(field_name="bean__bean_type")
    origin_country = CharFilter(field_name="bean__origin_country", lookup_expr="icontains")
    min_star = NumberFilter(field_name="taste_review__star", lookup_expr="gte")
    max_star = NumberFilter(field_name="taste_review__star", lookup_expr="lte")
    is_decaf = BooleanFilter(field_name="bean__is_decaf")
    sort_by = ChoiceFilter(choices=SORT_CHOICES, method="filter_sort_by")

    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(content__icontains=value)
            | Q(bean__name__icontains=value)
            | Q(tag__icontains=value)
            | Q(taste_review__flavor__icontains=value)
        )

    def filter_sort_by(self, queryset, name, value):
        if value == "latest":
            return queryset.order_by("-created_at")
        elif value == "like_rank":
            return queryset.order_by("-likes")
        elif value == "star_rank":
            return queryset.order_by("-taste_review__star")
        return queryset

    class Meta:
        model = TastedRecord
        fields = ["q", "bean_type", "origin_country", "min_star", "max_star", "is_decaf", "sort_by"]


class PostFilter(FilterSet):
    """
    게시글 검색 필터
    """

    SORT_CHOICES = [
        ("latest", "최신순"),
        ("like_rank", "좋아요순"),
    ]

    q = CharFilter(method="filter_query")
    subject = CharFilter(field_name="subject")
    sort_by = ChoiceFilter(choices=SORT_CHOICES, method="filter_sort_by")

    def filter_query(self, queryset, name, value):
        return queryset.filter(Q(title__icontains=value) | Q(content__icontains=value))

    def filter_sort_by(self, queryset, name, value):
        if value == "latest":
            return queryset.order_by("-created_at")
        elif value == "like_rank":
            return queryset.order_by("-likes")
        return queryset

    class Meta:
        model = Post
        fields = ["q", "subject", "sort_by"]
