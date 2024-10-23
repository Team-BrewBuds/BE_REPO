from django_filters import rest_framework as filters

from repo.records.models import TastedRecord


class TastedRecordFilter(filters.FilterSet):
    bean_type = filters.ChoiceFilter(field_name="bean__bean_type", choices=[("single", "single"), ("blend", "blend")])
    origin_country = filters.CharFilter(field_name="bean__origin_country", lookup_expr="icontains")
    star_min = filters.NumberFilter(field_name="taste_review__star", lookup_expr="gte")
    star_max = filters.NumberFilter(field_name="taste_review__star", lookup_expr="lte")
    is_decaf = filters.BooleanFilter(field_name="bean__is_decaf")

    class Meta:
        model = TastedRecord
        fields = ["bean_type", "origin_country", "star_min", "star_max", "is_decaf"]
