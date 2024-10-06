from django.contrib import admin

from .models import Bean, BeanTaste, BeanTasteReview

admin.site.register(Bean)
admin.site.register(BeanTaste)
admin.site.register(BeanTasteReview)
