from rest_framework import serializers

from repo.profiles.models import CustomUser
from repo.profiles.serializers import UserSimpleSerializer


class BudyRecommendSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(source="*")
    follower_cnt = serializers.IntegerField()

    class Meta:
        model = CustomUser
        fields = ["user", "follower_cnt"]
