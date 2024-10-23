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
