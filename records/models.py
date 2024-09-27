from django.db import models

class Tasted_Record(models.Model):
    tasted_record_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('profiles.User', on_delete=models.CASCADE, verbose_name="작성자")
    bean = models.ForeignKey('beans.Bean', on_delete=models.CASCADE, verbose_name="원두")
    taste_and_review = models.OneToOneField('beans.Bean_Taste_Review', on_delete=models.CASCADE, verbose_name="맛&평가")
    content = models.TextField(verbose_name="노트 내용")
    view_cnt = models.IntegerField(default=0, verbose_name="조회수")
    like_cnt = models.ManyToManyField('profiles.User', related_name='like_tasted_records')
    is_private = models.BooleanField(default=False, verbose_name="비공개 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    tag = models.TextField(null=True, verbose_name="태그")  # 여러 태그 가능

    def __str__(self):
        return f"{self.user.nickname} - {self.bean.name}"

    class Meta:
        db_table = 'tasted_record'
        verbose_name = '시음 기록'
        verbose_name_plural = '시음 기록'

class Post(models.Model):
    post_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('profiles.User', on_delete=models.CASCADE, verbose_name="작성자")
    tasted_record = models.ForeignKey(Tasted_Record, on_delete=models.CASCADE, null=True, blank=True, verbose_name="관련 시음 기록")
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    subject = models.CharField(max_length=100, verbose_name="주제")
    view_cnt = models.IntegerField(default=0, verbose_name="조회수")
    like_cnt = models.ManyToManyField('profiles.User', related_name='like_posts')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    tag = models.TextField(null=True, verbose_name="태그")  # 여러 태그 가능

    def __str__(self):
        return f"{self.user.nickname} - {self.title}"

    class Meta:
        db_table = 'post'
        verbose_name = '게시글'
        verbose_name_plural = '게시글'

class Photo(models.Model):
    photo_id = models.AutoField(primary_key=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, verbose_name="관련 게시글")
    tasted_record = models.ForeignKey(Tasted_Record, on_delete=models.CASCADE, null=True, blank=True, verbose_name="관련 시음 기록")
    photo_url = models.URLField(max_length=500, verbose_name="사진 URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="업로드 일자")

    def __str__(self):
        if self.post:
            summery = f"Photo: {self.post.post_id}"
        else:
            summery = f"Photo: {self.tasted_record.tasted_record_id}"
        return summery

    class Meta:
        db_table = 'photo'
        verbose_name = '사진'
        verbose_name_plural = '사진'
