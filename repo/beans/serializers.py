from rest_framework import serializers

from .models import Bean, BeanTasteReview


class BeanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bean
        fields = "__all__"


class BeanTasteAndReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeanTasteReview
        fields = "__all__"
