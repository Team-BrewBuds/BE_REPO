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


class PhotoDetailSerializer(PhotoSerializer):
    is_representative = serializers.SerializerMethodField()

    def get_is_representative(self, obj):
        return obj.photo_url.name.split("/")[-1].startswith("main_")

    class Meta:
        model = Photo
        fields = ["id", "photo_url", "is_representative"]


class PhotoUploadSerializer(serializers.Serializer):
    photo_url = serializers.ListField(
        child=serializers.ImageField(), required=True, max_length=10, error_messages={"required": "photo_url은 필수 필드입니다."}
    )


class ObjectSerializer(serializers.Serializer):
    object_type = serializers.ChoiceField(choices=["post", "tasted_record"])
    object_id = serializers.IntegerField()


class PhotoUpdateSerializer(PhotoUploadSerializer, ObjectSerializer):
    class Meta:
        fields = ["photo_url", "object_type", "object_id"]
