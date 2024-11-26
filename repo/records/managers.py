from datetime import timedelta

from django.db import models
from django.utils import timezone


class PostManagers(models.Manager):

    def get_subject_posts(self, subject):
        from .models import Post

        posts = Post.objects.filter(subject=subject)
        return posts

    def get_subject_weekly_posts(self, subject):
        from .models import Post

        time_threshold = timezone.now() - timedelta(days=7)
        posts = Post.objects.filter(created_at__gte=time_threshold)
        if subject is not None:
            posts = posts.filter(subject=subject)

        return posts
