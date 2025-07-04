

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gitlab_classroom', '0019_alter_assessment_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupProject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField()),
                ('deadline', models.DateTimeField(help_text='The deadline of the project')),
                ('students', models.ManyToManyField(related_name='student_groups', to='gitlab_classroom.student')),
                ('teacher', models.ManyToManyField(related_name='group_projects', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-name'],
            },
        ),
    ]
