# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion
import pinax.submissions.utils
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('text', models.TextField(verbose_name='Text')),
                ('text_html', models.TextField(blank=True)),
                ('public', models.BooleanField(default=False, choices=[(True, 'public'), (False, 'private')], verbose_name='Public')),
                ('commented_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Commented at')),
                ('commenter', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Commenter')),
            ],
            options={
                'verbose_name': 'comment',
                'verbose_name_plural': 'comments',
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('label', models.CharField(verbose_name='Label', max_length=100)),
                ('from_address', models.EmailField(verbose_name='From address', max_length=254)),
                ('subject', models.CharField(verbose_name='Subject', max_length=100)),
                ('body', models.TextField(verbose_name='Body')),
            ],
            options={
                'verbose_name': 'notification template',
                'verbose_name_plural': 'notification templates',
            },
        ),
        migrations.CreateModel(
            name='ResultNotification',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Timestamp')),
                ('to_address', models.EmailField(verbose_name='To address', max_length=254)),
                ('from_address', models.EmailField(verbose_name='From address', max_length=254)),
                ('subject', models.CharField(verbose_name='Subject', max_length=100)),
                ('body', models.TextField(verbose_name='Body')),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('comment', models.TextField(verbose_name='Comment')),
                ('comment_html', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Submitted at')),
            ],
            options={
                'verbose_name': 'review',
                'verbose_name_plural': 'reviews',
            },
        ),
        migrations.CreateModel(
            name='ReviewAssignment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('origin', models.IntegerField(choices=[(0, 'auto-assigned, initial'), (1, 'opted-in'), (2, 'auto-assigned, later')], verbose_name='Origin')),
                ('assigned_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Assigned at')),
                ('opted_out', models.BooleanField(default=False, verbose_name='Opted out')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionBase',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('submitted', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Submitted')),
                ('cancelled', models.BooleanField(default=False, verbose_name='Cancelled')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionKind',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(verbose_name='Name', max_length=100)),
                ('slug', models.SlugField(verbose_name='Slug')),
            ],
        ),
        migrations.CreateModel(
            name='SubmissionMessage',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('message', models.TextField(verbose_name='Message')),
                ('message_html', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Submitted at')),
                ('submission', models.ForeignKey(to='submissions.SubmissionBase', related_name='messages', verbose_name='Submission')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name_plural': 'submission messages',
                'ordering': ['submitted_at'],
                'verbose_name': 'submission message',
            },
        ),
        migrations.CreateModel(
            name='SubmissionResult',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('status', models.CharField(default='undecided', choices=[('accepted', 'accepted'), ('rejected', 'rejected'), ('undecided', 'undecided'), ('standby', 'standby')], verbose_name='Status', max_length=20)),
                ('submission', models.OneToOneField(to='submissions.SubmissionBase', related_name='result', verbose_name='Submission')),
            ],
            options={
                'verbose_name': 'submission result',
                'verbose_name_plural': 'submission results',
            },
        ),
        migrations.CreateModel(
            name='SupportingDocument',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created at')),
                ('document', models.FileField(verbose_name='Document', upload_to=pinax.submissions.models.uuid_filename)),
                ('description', models.CharField(verbose_name='Description', max_length=140)),
                ('submission', models.ForeignKey(to='submissions.SubmissionBase', related_name='supporting_documents', verbose_name='Submission')),
                ('uploaded_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Uploaded by')),
            ],
        ),
        migrations.AddField(
            model_name='submissionbase',
            name='kind',
            field=models.ForeignKey(to='submissions.SubmissionKind', verbose_name='Kind'),
        ),
        migrations.AddField(
            model_name='submissionbase',
            name='submitter',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='reviewassignment',
            name='submission',
            field=models.ForeignKey(to='submissions.SubmissionBase', verbose_name='Submission'),
        ),
        migrations.AddField(
            model_name='reviewassignment',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='review',
            name='submission',
            field=models.ForeignKey(to='submissions.SubmissionBase', related_name='reviews', verbose_name='Submission'),
        ),
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AddField(
            model_name='resultnotification',
            name='submission',
            field=models.ForeignKey(to='submissions.SubmissionBase', related_name='notifications', verbose_name='Submission'),
        ),
        migrations.AddField(
            model_name='resultnotification',
            name='template',
            field=models.ForeignKey(to='submissions.NotificationTemplate', on_delete=django.db.models.deletion.SET_NULL, null=True, blank=True, verbose_name='Template'),
        ),
        migrations.AddField(
            model_name='comment',
            name='submission',
            field=models.ForeignKey(to='submissions.SubmissionBase', related_name='comments', verbose_name='Submission'),
        ),
    ]
