from django.contrib import admin
from rangefilter.filters import NumericRangeFilter

from .models import Bean, BeanTaste, BeanTasteReview


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
        "bev_type",
    ]
    list_filter = ["bean_type", "is_decaf", "is_user_created", "origin_country"]
    search_fields = ["name"]


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
    list_display = ["id", "flavor", "body", "acidity", "bitterness", "sweetness", "star", "created_at", "place"]
    list_filter = ["star", "created_at", "place"]
    search_fields = ["flavor"]
