# Generated by Django 5.1.4 on 2025-05-08 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beans", "0009_alter_beantastereview_place"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bean",
            name="bean_type",
            field=models.CharField(
                choices=[("single", "싱글 오리진"), ("blend", "블렌드")],
                max_length=20,
                verbose_name="원두 유형",
            ),
        ),
    ]
