# Generated by Django 5.1.1 on 2024-09-26 07:10

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('beans', '0001_initial'),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('post_id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='제목')),
                ('content', models.TextField(verbose_name='내용')),
                ('subject', models.CharField(max_length=100, verbose_name='주제')),
                ('view_cnt', models.IntegerField(default=0, verbose_name='조회수')),
                ('like_cnt', models.IntegerField(default=0, verbose_name='좋아요 수')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='작성일')),
                ('tag', models.TextField(null=True, verbose_name='태그')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.user', verbose_name='작성자')),
            ],
            options={
                'verbose_name': '게시글',
                'verbose_name_plural': '게시글',
                'db_table': 'post',
            },
        ),
        migrations.CreateModel(
            name='Tasted_Record',
            fields=[
                ('tasted_record_id', models.AutoField(primary_key=True, serialize=False)),
                ('content', models.TextField(verbose_name='노트 내용')),
                ('view_cnt', models.IntegerField(default=0, verbose_name='조회수')),
                ('like_cnt', models.IntegerField(default=0, verbose_name='좋아요 수')),
                ('is_private', models.BooleanField(default=False, verbose_name='비공개 여부')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='작성일')),
                ('tag', models.TextField(null=True, verbose_name='태그')),
                ('bean', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='beans.bean', verbose_name='원두')),
                ('taste_and_review', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='beans.bean_taste_review', verbose_name='맛&평가')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='profiles.user', verbose_name='작성자')),
            ],
            options={
                'verbose_name': '시음 기록',
                'verbose_name_plural': '시음 기록',
                'db_table': 'tasted_record',
            },
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('photo_id', models.AutoField(primary_key=True, serialize=False)),
                ('photo_url', models.URLField(max_length=500, verbose_name='사진 URL')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='업로드 일자')),
                ('post', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='records.post', verbose_name='관련 게시글')),
                ('tasted_record', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='records.tasted_record', verbose_name='관련 시음 기록')),
            ],
            options={
                'verbose_name': '사진',
                'verbose_name_plural': '사진',
                'db_table': 'photo',
            },
        ),
    ]