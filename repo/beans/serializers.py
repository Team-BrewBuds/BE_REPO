from rest_framework import serializers

from .models import Bean, BeanTasteReview


class BeanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bean
        fields = "__all__"


class BeanTasteReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeanTasteReview
        fields = "__all__"


class UserBeanSerializer(serializers.ModelSerializer):
    avg_star = serializers.DecimalField(max_digits=3, rounding="ROUND_HALF_UP", decimal_places=2, default=0)
    tasted_records_cnt = serializers.IntegerField()

    class Meta:
        model = Bean
        fields = ["id", "name", "origin_country", "roast_point", "avg_star", "tasted_records_cnt"]


class BeanDetailSerializer(serializers.ModelSerializer):
    avg_star = serializers.DecimalField(max_digits=2, decimal_places=1, default=0)
    record_count = serializers.IntegerField(default=0)
    top_flavors = serializers.ListField(default=[])
    is_user_noted = serializers.BooleanField(default=False)

    flavor = serializers.CharField(source="bean_taste.flavor", read_only=True)
    body = serializers.IntegerField(source="bean_taste.body", read_only=True)
    acidity = serializers.IntegerField(source="bean_taste.acidity", read_only=True)
    bitterness = serializers.IntegerField(source="bean_taste.bitterness", read_only=True)
    sweetness = serializers.IntegerField(source="bean_taste.sweetness", read_only=True)

    image_url = serializers.URLField()

    class Meta:
        model = Bean
        fields = [
            "id",
            "name",
            "bean_type",
            "is_decaf",
            "origin_country",
            "region",
            "process",
            "roast_point",
            "avg_star",
            "record_count",
            "flavor",
            "body",
            "acidity",
            "bitterness",
            "sweetness",
            "image_url",
            "top_flavors",
            "is_user_noted",
        ]
