from django.contrib import admin

from .models import Photo, Post, TastedRecord, Comment, Note

admin.site.register(TastedRecord)
admin.site.register(Post)
admin.site.register(Photo)
admin.site.register(Comment)
admin.site.register(Note)