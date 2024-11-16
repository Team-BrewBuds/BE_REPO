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

    class PhotoField(serializers.ImageField):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.max_length = 5 * 1024 * 1024  # 5MB 제한
            self.error_messages.update(
                {
                    "invalid_image": "업로드한 파일이 이미지가 아니거나 손상된 이미지입니다 .",
                }
            )

    photo_url = serializers.ListField(
        child=PhotoField(),
        required=True,
        min_length=1,
        max_length=10,
        error_messages={
            "required": "photo_url은 필수 필드입니다.",
            "max_length": "최대 10개의 이미지만 업로드할 수 있습니다.",
            "min_length": "최소 1개의 이미지를 업로드해야 합니다.",
        },
    )


class ObjectSerializer(serializers.Serializer):
    object_type = serializers.ChoiceField(choices=["post", "tasted_record"])
    object_id = serializers.IntegerField()


class PhotoUpdateSerializer(PhotoUploadSerializer, ObjectSerializer):
    class Meta:
        fields = ["photo_url", "object_type", "object_id"]
