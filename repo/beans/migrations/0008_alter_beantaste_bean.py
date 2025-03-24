# Generated by Django 5.1.4 on 2025-03-11 14:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("beans", "0007_notusedbean"),
    ]

    operations = [
        migrations.AlterField(
            model_name="beantaste",
            name="bean",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bean_taste",
                to="beans.bean",
                verbose_name="공식 원두 기본 맛",
            ),
        ),
    ]
