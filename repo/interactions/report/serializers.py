from rest_framework import serializers

from repo.common.exception.exceptions import ValidationException


class BaseReportSerializer(serializers.Serializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    reason = serializers.CharField(required=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate(self, data):
        if not data.get("reason"):
            raise ValidationException(message="reason is required", code="reason_required")
        return data


class ContentReportSerializer(BaseReportSerializer):
    target_author = serializers.CharField(read_only=True)
    object_type = serializers.CharField(read_only=True)
    object_id = serializers.IntegerField(read_only=True)


class UserReportSerializer(BaseReportSerializer):
    target_user = serializers.CharField(source="target_user.nickname", read_only=True)
