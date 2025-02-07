from django.contrib import admin
from rangefilter.filters import NumericRangeFilter

from .models import Bean, BeanTaste, BeanTasteReview, NotUsedBean


class BeanTasteInline(admin.TabularInline):
    model = BeanTaste
    min_num = 1
    max_num = 1


@admin.register(Bean)
class BeanAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "bean_type",
        "origin_country",
        "extraction",
        "roast_point",
        "process",
        "region",
        "roastery",
        "variety",
        "is_decaf",
        "is_user_created",
        "is_official",
        "bev_type",
    ]
    list_filter = ["bean_type", "is_decaf", "is_user_created", "is_official", "origin_country"]
    search_fields = ["name"]

    def get_inlines(self, request, obj=None):
        if obj and obj.is_official:
            return [BeanTasteInline]
        return []


@admin.register(BeanTaste)
class BeanTasteAdmin(admin.ModelAdmin):
    list_display = ["id", "flavor", "body", "acidity", "bitterness", "sweetness"]
    list_filter = [
        "flavor",
        ("body", NumericRangeFilter),
        ("acidity", NumericRangeFilter),
        ("bitterness", NumericRangeFilter),
        ("sweetness", NumericRangeFilter),
    ]
    search_fields = ["flavor"]


@admin.register(BeanTasteReview)
class BeanTasteReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "flavor", "body", "acidity", "bitterness", "sweetness", "star", "tasted_at", "place"]
    list_filter = ["star", "tasted_at", "place"]
    search_fields = ["flavor"]


@admin.register(NotUsedBean)
class UserDeletedBeanAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "bean_type",
        "origin_country",
        "extraction",
        "roast_point",
        "process",
        "region",
        "roastery",
        "variety",
        "bev_type",
        "is_decaf",
        "is_user_created",
        "is_official",
    ]
    list_filter = ["bean_type", "is_user_created", "is_official"]
    search_fields = ["name"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "tastedrecord_set",
                "note_set",
            )
            .filter(
                tastedrecord__isnull=True,
                note__isnull=True,
                is_user_created=True,
                is_official=False,
            )
        )
