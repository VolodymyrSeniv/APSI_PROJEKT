# Generated by Django 4.2.7 on 2025-05-14 12:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gitlab_classroom', '0015_assignment_template_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='classroom',
            name='teacher',
        ),
        migrations.AddField(
            model_name='classroom',
            name='created_by',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='classroom_created_by', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='classroom',
            name='teachers',
            field=models.ManyToManyField(related_name='classroom_teachers', to=settings.AUTH_USER_MODEL),
        ),
    ]
