from rest_framework import serializers

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.profiles.serializers import UserSimpleSerializer


class BudyRecommendSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(source="*")
    follower_cnt = serializers.IntegerField()

    class Meta:
        model = CustomUser
        fields = ["user", "follower_cnt"]


class BeanRecommendSerializer(serializers.ModelSerializer):
    avg_star = serializers.FloatField()
    record_cnt = serializers.IntegerField()

    class Meta:
        model = Bean
        fields = ["id", "name", "image_url", "avg_star", "record_cnt"]
