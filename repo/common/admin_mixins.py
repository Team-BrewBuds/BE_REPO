from django.contrib import admin
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter


class CreatedAtMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = (self.list_display or []) + ["created_at"]
        self.list_filter = (self.list_filter or []) + ["created_at", ("created_at", DateRangeFilter)]


class AuthorMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = (self.list_display or []) + ["author_link"]

    @admin.display(description="작성자")
    def author_link(self, obj):
        url = f"/admin/profiles/customuser/{obj.author.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.author.nickname)


class RecordsInfoMixin(CreatedAtMixin, AuthorMixin):
    @admin.display(description="좋아요 수")
    def likes(self, obj):
        return obj.like_cnt.count()


class RelatedRecordsMixin(CreatedAtMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_display = [self.list_display[0], "post_link", "tasted_record_link"] + self.list_display[1:]

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
