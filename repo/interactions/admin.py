from django.contrib import admin

from repo.interactions.note.models import Note
from repo.interactions.relationship.models import Relationship
from repo.interactions.report.models import Report


class ReportAdmin(admin.ModelAdmin):
    list_display = ["author", "object_type", "reason", "object_id", "status", "created_at"]
    list_filter = ["status", "object_type", "reason", "created_at"]
    search_fields = ["author__username", "object_type", "object_id"]
    ordering = ["id"]


admin.site.register(Relationship)
admin.site.register(Note)
admin.site.register(Report, ReportAdmin)
