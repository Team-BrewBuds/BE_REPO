from rest_framework import serializers

from .models import Bean, BeanTaste, BeanTasteReview


class BeanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bean
        fields = "__all__"


class BeanTasteReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeanTasteReview
        fields = "__all__"


class BeanTasteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeanTaste
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
    bean_taste = BeanTasteSerializer(read_only=True)

    image_url = serializers.URLField()

    class Meta:
        model = Bean
        fields = "__all__"


class BeanRankingSerializer(serializers.Serializer):
    bean_id = serializers.IntegerField()
    bean__name = serializers.CharField()
