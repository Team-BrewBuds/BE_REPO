from django.db import models

from repo.beans.models import Bean
from repo.profiles.models import CustomUser
from repo.records.models import Post, TastedRecord


class Note(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="작성자")
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, verbose_name="게시글")
    tasted_record = models.ForeignKey(TastedRecord, null=True, blank=True, on_delete=models.CASCADE, verbose_name="시음 기록")
    bean = models.ForeignKey(Bean, null=True, blank=True, on_delete=models.CASCADE, verbose_name="원두")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    def __str__(self):
        return f"Note: {self.id}"

    class Meta:
        db_table = "note"
        verbose_name = "노트"
        verbose_name_plural = "노트"
