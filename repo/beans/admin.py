from django.contrib import admin

from .models import Bean, BeanTaste, BeanTasteReview


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


class BeanTasteAdmin(admin.ModelAdmin):
    list_display = ["id", "flavor", "body", "acidity", "bitterness", "sweetness"]
    search_fields = ["flavor"]


class BeanTasteReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "flavor", "body", "acidity", "bitterness", "sweetness", "star", "created_at", "place"]
    list_filter = ["star", "created_at", "place"]
    search_fields = ["flavor"]


admin.site.register(Bean, BeanAdmin)
admin.site.register(BeanTaste, BeanTasteAdmin)
admin.site.register(BeanTasteReview, BeanTasteReviewAdmin)
