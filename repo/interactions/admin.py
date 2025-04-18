from django.contrib import admin
from django.utils.html import format_html

from repo.common.admin_mixins import CreatedAtMixin, RelatedRecordsMixin
from repo.interactions.note.models import Note
from repo.interactions.relationship.models import Relationship
from repo.interactions.report.models import ContentReport, UserReport
from repo.records.models import Comment


@admin.register(ContentReport)
class ContentReportAdmin(CreatedAtMixin, admin.ModelAdmin):
    list_display = ["id", "author_link", "object_type", "reason", "object_link", "status"]
    list_filter = ["object_type", "reason", "status"]
    search_fields = ["author__username", "object_type", "object_id"]
    readonly_fields = ["related_comment"]

    @admin.display(description="신고자")
    def author_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.author.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.author.nickname)

    @admin.display(description="신고 대상")
    def object_link(self, obj):
        if obj.object_type == "tasted_record":
            obj.object_type = "tastedrecord"
        url = f"/admin/records/{obj.object_type}/{obj.object_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.object_id)

    def related_comment(self, obj):
        if obj.object_type == "comment":
            comment = Comment.objects.filter(id=obj.object_id).first()
            parent_comment = Comment.objects.filter(id=comment.parent.id).first() if comment.parent else None
            comments = Comment.objects.filter(parent=comment.parent.id).order_by("id").values_list("id", "author__nickname", "content")
            results = [
                f"상위 댓글 ID: {parent_comment.id}, 닉네임: {parent_comment.author.nickname}, 내용: {parent_comment.content}",
                "대댓글",
                "\n".join([f"ID: {comment[0]}, 닉네임: {comment[1]}, 내용: {comment[2]}" for comment in comments]),
            ]
            return "\n".join(results)
        else:  # post or tasted_record
            object_type = "post" if obj.object_type == "post" else "tasted_record"
            object_id = obj.object_id
            comments = Comment.objects.filter(**{object_type: object_id}).order_by("id").values_list("id", "author__nickname", "content")
            return "\n".join([f"ID: {comment[0]}, 닉네임: {comment[1]}, 내용: {comment[2]}" for comment in comments])


@admin.register(UserReport)
class UserReportAdmin(CreatedAtMixin, admin.ModelAdmin):
    list_display = ["id", "author_link", "target_user_link", "reason", "status"]
    list_filter = ["reason", "status"]
    search_fields = ["author__username", "target_user__username"]

    @admin.display(description="신고자")
    def author_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.author.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.author.nickname)

    @admin.display(description="신고 대상")
    def target_user_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.target_user.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.target_user.nickname)


@admin.register(Note)
class NoteAdmin(RelatedRecordsMixin, admin.ModelAdmin):
    list_display = ["id", "bean_link", "author"]
    list_filter = [
        ("post", admin.EmptyFieldListFilter),
        ("tasted_record", admin.EmptyFieldListFilter),
        ("bean", admin.EmptyFieldListFilter),
    ]

    @admin.display(description="작성자")
    def author(self, obj):
        return obj.author.nickname

    @admin.display(description="원두")
    def bean_link(self, obj):
        if obj.bean:
            url = f"/admin/beans/bean/{obj.bean.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.bean.name)


@admin.register(Relationship)
class RelationshipAdmin(CreatedAtMixin, admin.ModelAdmin):
    list_display = ["id", "from_user_link", "relationship_type", "to_user_link"]
    list_filter = ["relationship_type"]

    @admin.display(description="신고자")
    def from_user_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.from_user.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.from_user.nickname)

    @admin.display(description="신고 대상")
    def to_user_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.to_user.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.to_user.nickname)
