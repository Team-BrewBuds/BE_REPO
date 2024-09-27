from django.contrib import admin

from .models import Photo, Post, Tasted_Record

admin.site.register(Tasted_Record)
admin.site.register(Post)
admin.site.register(Photo)
