# Generated by Django 5.1.2 on 2024-10-19 20:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('records', '0007_merge_20241018_2357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='photo_url',
            field=models.ImageField(blank=True, null=True, upload_to='records/', verbose_name='사진'),
        ),
    ]
