# Generated by Django 5.1.4 on 2025-01-18 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("records", "0011_tastedrecord_tasted_at"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tastedrecord",
            name="tasted_at",
            field=models.DateField(blank=True, null=True, verbose_name="시음일"),
        ),
    ]
