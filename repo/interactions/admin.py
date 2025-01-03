from django.contrib import admin
from django.utils.html import format_html

from repo.interactions.note.models import Note
from repo.interactions.relationship.models import Relationship
from repo.interactions.report.models import Report


class ReportAdmin(admin.ModelAdmin):
    list_display = ["id", "author_link", "object_type", "reason", "object_link", "status", "created_at"]
    list_filter = ["status", "object_type", "reason", "created_at"]
    search_fields = ["author__username", "object_type", "object_id"]
    ordering = ["id"]

    @admin.display(description="신고자")
    def author_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.author.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.author.nickname)

    @admin.display(description="신고 대상")
    def object_link(self, obj):
        if obj.object_type == "post":
            url = f"/admin/records/post/{obj.object_id}/change/"
        elif obj.object_type == "tasted_record":
            url = f"/admin/records/tastedrecord/{obj.object_id}/change/"
        elif obj.object_type == "comment":
            url = f"/admin/records/comment/{obj.object_id}/change/"
        else:
            return obj.object_id
        return format_html('<a href="{}">{}</a>', url, obj.object_id)


admin.site.register(Relationship)
admin.site.register(Note)
admin.site.register(Report, ReportAdmin)
