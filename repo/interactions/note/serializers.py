from rest_framework import serializers

from repo.beans.models import Bean
from repo.common.exception.exceptions import ValidationException
from repo.records.models import Post, TastedRecord

from .models import Note

VALID_OBJECT_TYPES = ["post", "tasted_record", "bean"]


class NoteCreateSerializer(serializers.Serializer):
    object_type = serializers.ChoiceField(choices=VALID_OBJECT_TYPES)
    object_id = serializers.IntegerField(min_value=1)

    def validate(self, data):
        """
        객체 타입, 존재 여부 검증
        """
        object_type = data["object_type"]
        object_id = data["object_id"]

        model_map = {"post": Post, "tasted_record": TastedRecord, "bean": Bean}

        if object_type not in VALID_OBJECT_TYPES:
            raise ValidationException(message=f"Invalid object type: {object_type}", code="invalid_object_type")

        model = model_map[object_type]
        if not model.objects.filter(id=object_id).exists():
            raise ValidationException(message=f"{object_type} with id {object_id} does not exist", code="object_not_found")

        return data


class NoteResponseSerializer(serializers.ModelSerializer):
    post = serializers.IntegerField(source="post.id", required=False)
    tasted_record = serializers.IntegerField(source="tasted_record.id", required=False)
    bean = serializers.IntegerField(source="bean.id", required=False)

    class Meta:
        model = Note
        fields = "__all__"
