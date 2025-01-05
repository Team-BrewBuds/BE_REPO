from django_filters import rest_framework as filters

from repo.beans.models import Bean
from repo.records.models import TastedRecord


class TastedRecordFilter(filters.FilterSet):
    bean_type = filters.ChoiceFilter(field_name="bean__bean_type", choices=[("single", "싱글 오리진"), ("blend", "블렌드")])
    origin_country = filters.CharFilter(field_name="bean__origin_country", lookup_expr="icontains")
    is_decaf = filters.BooleanFilter(field_name="bean__is_decaf")
    star_min = filters.NumberFilter(field_name="taste_review__star", lookup_expr="gte")
    star_max = filters.NumberFilter(field_name="taste_review__star", lookup_expr="lte")
    roast_point_min = filters.NumberFilter(field_name="bean__roast_point", lookup_expr="gte")
    roast_point_max = filters.NumberFilter(field_name="bean__roast_point", lookup_expr="lte")

    class Meta:
        model = TastedRecord
        fields = ["bean_type", "origin_country", "is_decaf", "star_min", "star_max", "roast_point_min", "roast_point_max"]


class BeanFilter(filters.FilterSet):
    bean_type = filters.ChoiceFilter(choices=[("single", "싱글 오리진"), ("blend", "블렌드")])
    origin_country = filters.CharFilter(lookup_expr="icontains")
    is_decaf = filters.BooleanFilter()
    avg_star_min = filters.NumberFilter(field_name="avg_star", lookup_expr="gte")
    avg_star_max = filters.NumberFilter(field_name="avg_star", lookup_expr="lte")
    roast_point_min = filters.NumberFilter(field_name="roast_point", lookup_expr="gte")
    roast_point_max = filters.NumberFilter(field_name="roast_point", lookup_expr="lte")

    class Meta:
        model = Bean
        fields = ["bean_type", "origin_country", "is_decaf", "roast_point_min", "roast_point_max", "avg_star_min", "avg_star_max"]
