from django.contrib import admin
from django.utils.html import format_html

from repo.common.admin_filters import IsPublicFilter
from repo.common.admin_mixins import RecordsInfoMixin, RelatedRecordsMixin

from .models import Comment, Photo, Post, TastedRecord


@admin.register(TastedRecord)
class TastedRecordAdmin(RecordsInfoMixin, admin.ModelAdmin):
    list_display = ["id", "bean", "view_cnt", "is_public"]
    list_filter = [IsPublicFilter]
    search_fields = ["author__username", "bean__name"]
    actions = ["make_tasted_record_private", "make_tasted_record_public"]
    list_select_related = ["author", "bean"]

    @admin.display(description="공개 여부", boolean=True)
    def is_public(self, obj):
        return not obj.is_private

    @admin.action(description="비공개로 수정")
    def make_tasted_record_private(self, request, queryset):
        queryset.update(is_private=True)
        self.message_user(request, f"{queryset.count()} 개의 시음기록이 비공개로 수정되었습니다.")

    @admin.action(description="공개로 수정")
    def make_tasted_record_public(self, request, queryset):
        queryset.update(is_private=False)
        self.message_user(request, f"{queryset.count()} 개의 시음기록이 공개로 수정되었습니다.")


@admin.register(Post)
class PostAdmin(RecordsInfoMixin, admin.ModelAdmin):
    list_display = ["id", "subject", "title", "view_cnt"]
    list_filter = ["subject"]
    search_fields = ["author__username", "title"]


@admin.register(Comment)
class CommentAdmin(RecordsInfoMixin, admin.ModelAdmin):
    list_display = ["id", "get_comment_content", "get_parent_content", "post_link", "tasted_record_link"]
    list_filter = [
        ("post", admin.EmptyFieldListFilter),
        ("tasted_record", admin.EmptyFieldListFilter),
    ]
    search_fields = ["author__username", "post__title", "content"]

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


@admin.register(Photo)
class PhotoAdmin(RelatedRecordsMixin, admin.ModelAdmin):
    list_display = ["id", "author"]
    list_filter = [("post", admin.EmptyFieldListFilter), ("tasted_record", admin.EmptyFieldListFilter)]

    @admin.display(description="작성자")
    def author(self, obj):
        if obj.post:
            return obj.post.author
        elif obj.tasted_record:
            return obj.tasted_record.author
        return None
