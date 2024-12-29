from django.contrib import admin

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
    list_display = ["author", "get_comment_content", "post", "tasted_record", "created_at"]
    list_filter = [
        ("post", admin.EmptyFieldListFilter),
        ("tasted_record", admin.EmptyFieldListFilter),
        "created_at",
    ]
    search_fields = ["author__username", "post__title", "content"]

    def get_comment_content(self, obj):
        return obj.content[:20] + "..." if not obj.is_deleted else "삭제된 댓글"

    get_comment_content.short_description = "댓글 내용"


admin.site.register(TastedRecord, TastedRecordAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Photo)
admin.site.register(Comment, CommentAdmin)
