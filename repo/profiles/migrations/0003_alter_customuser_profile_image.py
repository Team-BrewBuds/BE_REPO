# Generated by Django 5.1.1 on 2024-10-09 19:34

from django.db import migrations, models

import repo.common.bucket


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0002_userdetail"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="profile_image",
            field=models.ImageField(blank=True, null=True, upload_to=repo.common.bucket.photo_upload_to),
        ),
    ]
