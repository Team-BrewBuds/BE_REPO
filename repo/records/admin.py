from django.contrib import admin
from django.utils.html import format_html

from .models import Comment, Photo, Post, TastedRecord


class TastedRecordAdmin(admin.ModelAdmin):
    list_display = ["author", "bean", "view_cnt", "created_at", "is_private"]
    list_filter = ["created_at", "is_private"]
    search_fields = ["author__username", "bean__name"]
    actions = ["make_tasted_record_private", "make_tasted_record_public"]

    @admin.action(description="비공개로 수정")
    def make_tasted_record_private(self, request, queryset):
        queryset.update(is_private=True)
        self.message_user(request, f"{queryset.count()} 개의 시음기록이 비공개로 수정되었습니다.")

    @admin.action(description="공개로 수정")
    def make_tasted_record_public(self, request, queryset):
        queryset.update(is_private=False)
        self.message_user(request, f"{queryset.count()} 개의 시음기록이 공개로 수정되었습니다.")


class PostAdmin(admin.ModelAdmin):
    list_display = ["author", "title", "view_cnt", "subject", "created_at"]
    list_filter = ["subject", "created_at"]
    search_fields = ["author__username", "title"]


class CommentAdmin(admin.ModelAdmin):
    list_display = ["id", "author_link", "get_comment_content", "get_parent_content", "post_link", "tasted_record_link", "created_at"]
    list_filter = [
        ("post", admin.EmptyFieldListFilter),
        ("tasted_record", admin.EmptyFieldListFilter),
        "created_at",
    ]
    search_fields = ["author__username", "post__title", "content"]

    @admin.display(description="작성자")
    def author_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.author.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.author.nickname)

    @admin.display(description="댓글 내용")
    def get_comment_content(self, obj):
        return obj.content[:20] + "..." if not obj.is_deleted else "삭제된 댓글"

    @admin.display(description="상위 댓글 내용")
    def get_parent_content(self, obj):
        return obj.parent.content[:20] + "..." if obj.parent else "상위 댓글 없음"

    @admin.display(description="게시글")
    def post_link(self, obj):
        if obj.post:
            url = f"/admin/records/post/{obj.post.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.post.title[:20] + "...")

    @admin.display(description="시음 기록")
    def tasted_record_link(self, obj):
        if obj.tasted_record:
            url = f"/admin/records/tastedrecord/{obj.tasted_record.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.tasted_record.bean.name[:20] + "...")


admin.site.register(TastedRecord, TastedRecordAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Photo)
admin.site.register(Comment, CommentAdmin)
