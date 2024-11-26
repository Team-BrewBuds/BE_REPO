from rest_framework import serializers

from repo.common.exception.exceptions import ValidationException

from .models import Report


class ReportSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.nickname", read_only=True)
    target_author = serializers.CharField(read_only=True)
    object_type = serializers.CharField(read_only=True)
    object_id = serializers.IntegerField(read_only=True)
    reason = serializers.CharField(required=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate(self, data):
        if not data.get("reason"):
            raise ValidationException(message="reason is required", code="reason_required")
        return data

    class Meta:
        model = Report
        fields = "__all__"
