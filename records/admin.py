from django.contrib import admin

from .models import Photo, Post, Tasted_Record, Comment

admin.site.register(Tasted_Record)
admin.site.register(Post)
admin.site.register(Photo)
admin.site.register(Comment)