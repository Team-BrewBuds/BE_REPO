from django.contrib import admin

from .models import Comment, Note, Photo, Post, TastedRecord

admin.site.register(TastedRecord)
admin.site.register(Post)
admin.site.register(Photo)
admin.site.register(Comment)
admin.site.register(Note)
