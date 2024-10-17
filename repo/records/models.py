from django.db import models

from repo.common.bucket import photo_upload_to
from repo.beans.models import Bean, BeanTasteReview
from repo.profiles.models import CustomUser
from repo.records.managers import NoteManagers, PostManagers


class TastedRecord(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="작성자")
    bean = models.ForeignKey(Bean, on_delete=models.CASCADE, verbose_name="원두")
    taste_review = models.OneToOneField(BeanTasteReview, on_delete=models.CASCADE, verbose_name="맛&평가")
    content = models.TextField(verbose_name="노트 내용")
    view_cnt = models.IntegerField(default=0, verbose_name="조회수")
    like_cnt = models.ManyToManyField(CustomUser, default=0, related_name="like_tasted_records")
    is_private = models.BooleanField(default=False, verbose_name="비공개 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    tag = models.TextField(null=True, blank=True, verbose_name="태그")  # 여러 태그 가능

    def is_user_liked(self, user):
        return user in self.like_cnt.all()

    def __str__(self):
        return f"{self.author.nickname} - {self.bean.name}"

    class Meta:
        db_table = "tasted_record"
        verbose_name = "시음 기록"
        verbose_name_plural = "시음 기록"


class Post(models.Model):

    SUBJECT_TYPE_CHOICES = (
        ("전체", "all"),
        ("일반", "normal"),
        ("카페", "cafe"),
        ("원두", "bean"),
        ("정보", "info"),
        ("장비", "gear"),
        ("질문", "question"),
        ("고민", "worry"),
    )

    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="작성자")
    tasted_records = models.ManyToManyField(TastedRecord, blank=True, related_name="posts", verbose_name="관련 시음 기록")
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    subject = models.CharField(max_length=100, choices=SUBJECT_TYPE_CHOICES, verbose_name="주제")
    view_cnt = models.IntegerField(default=0, verbose_name="조회수")
    like_cnt = models.ManyToManyField(CustomUser, related_name="like_posts")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    tag = models.TextField(null=True, blank=True, verbose_name="태그")  # 여러 태그 가능

    objects = PostManagers()

    def is_user_liked(self, user):
        return user in self.like_cnt.all()

    def is_saved(self, user):
        return user.note_set.filter(post=self).exists()

    def comment_cnt(self):
        return self.comment_set.count()

    def __str__(self):
        return f"{self.author.nickname} - {self.title}"

    class Meta:
        db_table = "post"
        verbose_name = "게시글"
        verbose_name_plural = "게시글"


class Photo(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name="관련 게시글")
    tasted_record = models.ForeignKey(TastedRecord, on_delete=models.CASCADE, null=True, blank=True, verbose_name="관련 시음 기록")
    photo_url = models.ImageField(upload_to=photo_upload_to, null=True, blank=True, verbose_name="사진")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="업로드 일자")

    def __str__(self):
        return f"Photo: {self.post.id}" if self.post else f"Photo: {self.tasted_record.id}"

    class Meta:
        db_table = "photo"
        verbose_name = "사진"
        verbose_name_plural = "사진"


class Comment(models.Model):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies", verbose_name="상위 댓글")
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="작성자")
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, verbose_name="게시글")
    tasted_record = models.ForeignKey(TastedRecord, null=True, blank=True, on_delete=models.CASCADE, verbose_name="시음 기록")
    content = models.TextField(verbose_name="내용")
    like_cnt = models.ManyToManyField(CustomUser, related_name="like_comments")
    is_deleted = models.BooleanField(default=False, verbose_name="삭제 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    def __str__(self):
        return f"삭제된 댓글 ID: {self.id}" if self.is_deleted else f"{self.author.nickname} - {self.content[:20]}"

    class Meta:
        db_table = "comment"
        verbose_name = "댓글"
        verbose_name_plural = "댓글"


class Note(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="작성자")
    post = models.ForeignKey(Post, null=True, blank=True, on_delete=models.CASCADE, verbose_name="게시글")
    tasted_record = models.ForeignKey(TastedRecord, null=True, blank=True, on_delete=models.CASCADE, verbose_name="시음 기록")
    bean = models.ForeignKey(Bean, null=True, blank=True, on_delete=models.CASCADE, verbose_name="원두")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")

    # objects = models.Manager()  # The default manager
    objects = NoteManagers()

    def __str__(self):
        return f"Note: {self.id}"

    class Meta:
        db_table = "note"
        verbose_name = "노트"
        verbose_name_plural = "노트"
