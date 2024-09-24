from django.urls import path, include
urlpatterns = [
    path('posts/', include('records.posts.urls')),
    path('tasted_record/', include('records.tasted_record.urls')),
]