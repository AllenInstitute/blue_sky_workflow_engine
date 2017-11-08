# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-28 22:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Datafix',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('timestamp', models.CharField(max_length=255)),
                ('run_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Executable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.CharField(max_length=255, null=True)),
                ('static_arguments', models.CharField(max_length=255, null=True)),
                ('executable_path', models.CharField(max_length=1000)),
                ('pbs_executable_path', models.CharField(max_length=1000, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pbs_processor', models.CharField(default='vmem=6g', max_length=255)),
                ('pbs_walltime', models.CharField(default='walltime=5:00:00', max_length=255)),
                ('pbs_queue', models.CharField(default='lims', max_length=255)),
                ('version', models.CharField(default='0.1', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='FileRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('storage_directory', models.CharField(max_length=500)),
                ('order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enqueued_object_id', models.IntegerField()),
                ('duration', models.DurationField(null=True)),
                ('start_run_time', models.DateTimeField(null=True)),
                ('end_run_time', models.DateTimeField(null=True)),
                ('error_message', models.TextField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('priority', models.IntegerField(default=50)),
                ('archived', models.NullBooleanField(default=False)),
                ('tags', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='JobQueue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.CharField(max_length=255, null=True)),
                ('job_strategy_class', models.CharField(max_length=255)),
                ('enqueued_object_class', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('executable', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.Executable')),
            ],
        ),
        migrations.CreateModel(
            name='RunState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enqueued_task_object_id', models.IntegerField(null=True)),
                ('enqueued_task_object_class', models.CharField(max_length=255, null=True)),
                ('archived', models.NullBooleanField(default=False)),
                ('full_executable', models.CharField(max_length=1000, null=True)),
                ('error_message', models.TextField(null=True)),
                ('log_file', models.CharField(max_length=255, null=True)),
                ('input_file', models.CharField(max_length=255, null=True)),
                ('output_file', models.CharField(max_length=255, null=True)),
                ('pbs_file', models.CharField(max_length=255, null=True)),
                ('start_run_time', models.DateTimeField(null=True)),
                ('end_run_time', models.DateTimeField(null=True)),
                ('duration', models.DurationField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pbs_id', models.CharField(max_length=255, null=True)),
                ('retry_count', models.IntegerField(default=0)),
                ('tags', models.CharField(max_length=255, null=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.Job')),
                ('run_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.RunState')),
            ],
        ),
        migrations.CreateModel(
            name='WellKnownFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachable_id', models.PositiveIntegerField()),
                ('well_known_file_type', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attachable_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=255, null=True)),
                ('disabled', models.BooleanField(default=False)),
                ('use_pbs', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='WorkflowNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_head', models.BooleanField(default=False)),
                ('disabled', models.BooleanField(default=False)),
                ('batch_size', models.IntegerField(default=50)),
                ('priority', models.IntegerField(default=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('overwrite_previous_job', models.BooleanField(default=True)),
                ('max_retries', models.IntegerField(default=3)),
                ('job_queue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.JobQueue')),
                ('parent', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.WorkflowNode')),
                ('workflow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.Workflow')),
            ],
        ),
        migrations.AddField(
            model_name='job',
            name='run_state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.RunState'),
        ),
        migrations.AddField(
            model_name='job',
            name='workflow_node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.WorkflowNode'),
        ),
        migrations.AddField(
            model_name='filerecord',
            name='task',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.Task'),
        ),
        migrations.AddField(
            model_name='filerecord',
            name='well_known_file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workflow_engine.WellKnownFile'),
        ),
    ]
