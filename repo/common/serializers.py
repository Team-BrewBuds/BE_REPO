from rest_framework import serializers

from repo.records.models import Photo


class PageNumberSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)

    def validate_page(self, value):
        if value < 1:
            raise serializers.ValidationError("Page number must be a positive integer.")
        return value


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["photo_url"]
