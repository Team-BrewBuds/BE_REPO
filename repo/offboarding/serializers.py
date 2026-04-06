from rest_framework import serializers

from repo.offboarding.models import ExportRequest


class ExportRequestSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.nickname", read_only=True)

    class Meta:
        model = ExportRequest
        fields = ["user_id", "username", "export_email", "created_at"]
        read_only_fields = ["user_id", "username", "created_at"]


class ExportRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportRequest
        fields = ["export_email"]

    def validate_export_email(self, value):
        return value.lower().strip()
