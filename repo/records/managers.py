from datetime import timedelta

from django.apps import apps
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone


class PostManagers(models.Manager):

    def get_subject_posts(self, subject):
        from .models import Post

        posts = Post.objects.filter(subject=subject)
        return posts

    def get_subject_weekly_posts(self, subject):
        from .models import Post

        if subject == "all":
            # 전체 주제의 게시글 중 일주일 안에 작성된 게시글
            posts = Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=7))
        else:
            posts = Post.objects.filter(subject=subject, created_at__gte=timezone.now() - timedelta(days=7))

        return posts

    def get_top_subject_weekly_posts(self, subject):
        # 전체 주제의 게시글 중 일주일 안에 조회수 상위 10개
        posts = self.get_subject_weekly_posts(subject).order_by("-view_cnt")
        return posts


class NoteManagers(models.Manager):
    model_map = {"post": "repo.records.Post", "tasted_record": "repo.records.Tasted_Record", "bean": "repo.beans.Bean"}

    def create_note_for_object(self, user, object_type, object_id):
        from repo.records.models import Note

        model = self._get_model(object_type)
        obj = get_object_or_404(model, pk=object_id)

        note = Note.objects.create(author=user, **{f"{object_type}": obj})
        note.save()
        return note

    def existing_note(self, user, object_type, object_id):
        from repo.records.models import Note

        model = self._get_model(object_type)
        existing_note = Note.objects.filter(author=user, **{f"{object_type}__id": object_id}).first()

        return existing_note

    def _get_model(self, object_type):
        model_path = self.model_map.get(object_type)
        _, app_label, model_name = model_path.split(".")
        return apps.get_model(app_label, model_name)
