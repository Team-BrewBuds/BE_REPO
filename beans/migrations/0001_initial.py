# Generated by Django 5.1.1 on 2024-09-23 13:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bean',
            fields=[
                ('bean_id', models.AutoField(primary_key=True, serialize=False)),
                ('bean_type', models.CharField(choices=[('single', '싱글 오리진'), ('blend', '블랜드')], max_length=20, verbose_name='원두 유형')),
                ('is_decaf', models.BooleanField(default=False, verbose_name='디카페인')),
                ('name', models.CharField(max_length=100, verbose_name='원두명')),
                ('origin_country', models.CharField(max_length=100, verbose_name='원산지')),
                ('extraction', models.CharField(max_length=50, null=True, verbose_name='추출 방식')),
                ('roast_point', models.IntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], null=True, verbose_name='로스팅 포인트')),
                ('process', models.CharField(max_length=50, null=True, verbose_name='가공 방식')),
                ('region', models.CharField(max_length=100, null=True, verbose_name='지역')),
                ('bev_type', models.BooleanField(default=False, null=True, verbose_name='음료 유형')),
                ('roastery', models.CharField(max_length=100, null=True, verbose_name='로스터리')),
                ('variety', models.CharField(max_length=100, null=True, verbose_name='원두 품종')),
                ('is_user_created', models.DateTimeField(default=False, null=True, verbose_name='사용자 추가 여부')),
            ],
            options={
                'verbose_name': '원두',
                'verbose_name_plural': '원두',
                'db_table': 'bean',
            },
        ),
        migrations.CreateModel(
            name='Bean_Taste',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taste', models.TextField(verbose_name='맛')),
                ('body', models.IntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='바디감')),
                ('acidity', models.IntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='산미')),
                ('bitterness', models.IntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='쓴맛')),
                ('sweetness', models.IntegerField(choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], verbose_name='단맛')),
                ('bean', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='beans.bean', verbose_name='원두')),
            ],
            options={
                'verbose_name': '원두 맛',
                'verbose_name_plural': '원두 맛',
                'db_table': 'bean_taste',
            },
        ),
    ]
