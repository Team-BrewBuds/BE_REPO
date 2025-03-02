# Generated by Django 5.1.4 on 2025-01-31 16:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("records", "0014_remove_tastedrecord_tasted_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="likes",
            field=models.IntegerField(default=0, verbose_name="좋아요 수"),
        ),
        migrations.RunPython(
            lambda apps, schema_editor: update_likes_field(apps, schema_editor),
            reverse_code=lambda apps, schema_editor: update_likes_field(apps, schema_editor, reverse=True),
        ),
        # migrations.RunSQL(
        #     "UPDATE post SET likes = (SELECT COUNT(*) FROM post_like_cnt WHERE post_id = post.id)",
        #     reverse_sql="UPDATE post SET likes = 0",
        # ),
    ]


def update_likes_field(apps, schema_editor, reverse=False):

    Post = apps.get_model("records", "Post")
    if reverse:
        Post.objects.all().update(likes=0)
    else:
        for post in Post.objects.all():
            post.likes = post.like_cnt.count()
            post.save()
