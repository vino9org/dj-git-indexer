# Generated by Django 4.2.3 on 2023-10-01 14:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Author",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=128)),
                ("email", models.CharField(max_length=1024)),
                ("real_name", models.CharField(max_length=128)),
                ("real_email", models.CharField(max_length=1024)),
                ("company", models.CharField(max_length=64, null=True)),
                ("team", models.CharField(max_length=64, null=True)),
                ("author_group", models.CharField(max_length=64, null=True)),
                ("login_name", models.CharField(max_length=128, null=True)),
            ],
            options={
                "db_table": "authors",
            },
        ),
        migrations.CreateModel(
            name="Commit",
            fields=[
                ("sha", models.CharField(max_length=40, primary_key=True, serialize=False)),
                ("branches", models.CharField(default="", max_length=1024)),
                ("message", models.CharField(default="", max_length=2048)),
                ("created_at", models.DateTimeField(null=True)),
                ("is_merge", models.BooleanField(default=False)),
                ("n_lines", models.IntegerField(default=0)),
                ("n_files", models.IntegerField(default=0)),
                ("n_insertions", models.IntegerField(default=0)),
                ("n_deletions", models.IntegerField(default=0)),
                ("dmm_unit_size", models.FloatField(default=0.0)),
                ("dmm_unit_complexity", models.FloatField(default=0.0)),
                ("dmm_unit_interfacing", models.FloatField(default=0.0)),
                ("n_lines_changed", models.IntegerField(default=0)),
                ("n_lines_ignored", models.IntegerField(default=0)),
                ("n_files_changed", models.IntegerField(default=0)),
                ("n_files_ignored", models.IntegerField(default=0)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, related_name="commits", to="indexer.author"
                    ),
                ),
            ],
            options={
                "db_table": "commits",
            },
        ),
        migrations.CreateModel(
            name="Repository",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("repo_type", models.CharField(max_length=20)),
                ("repo_name", models.CharField(max_length=128)),
                ("repo_group", models.CharField(max_length=64, null=True)),
                ("component", models.CharField(max_length=64, null=True)),
                ("clone_url", models.CharField(max_length=256)),
                ("is_active", models.BooleanField(default=True)),
                ("last_indexed_at", models.DateTimeField(null=True)),
                ("last_commit_at", models.DateTimeField(null=True)),
            ],
            options={
                "verbose_name_plural": "repositories",
                "db_table": "repositories",
            },
        ),
        migrations.CreateModel(
            name="RepositoryCommitLink",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("commit", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to="indexer.commit")),
                ("repo", models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to="indexer.repository")),
            ],
            options={
                "db_table": "repo_to_commits",
            },
        ),
        migrations.AddField(
            model_name="repository",
            name="commits",
            field=models.ManyToManyField(through="indexer.RepositoryCommitLink", to="indexer.commit"),
        ),
        migrations.CreateModel(
            name="MergeRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_id", models.CharField(max_length=40)),
                ("title", models.CharField(max_length=1024)),
                ("state", models.CharField(max_length=32)),
                ("source_sha", models.CharField(default="", max_length=256)),
                ("source_branch", models.CharField(default="", max_length=256)),
                ("target_branch", models.CharField(default="", max_length=256, null=True)),
                ("merge_sha", models.CharField(default="", max_length=256, null=True)),
                ("created_at", models.DateTimeField(null=True)),
                ("merged_at", models.DateTimeField(null=True)),
                ("updated_at", models.DateTimeField(null=True)),
                ("first_comment_at", models.DateTimeField(null=True)),
                ("is_merged", models.BooleanField(default=False)),
                ("merged_by_username", models.CharField(max_length=32, null=True)),
                ("has_tests", models.BooleanField(default=False)),
                ("has_test_passed", models.BooleanField(default=False)),
                (
                    "repo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="merge_requests",
                        to="indexer.repository",
                    ),
                ),
            ],
            options={
                "db_table": "merge_requests",
            },
        ),
        migrations.CreateModel(
            name="CommittedFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("commit_sha", models.CharField(max_length=40)),
                ("change_type", models.CharField(default="UNKNOWN", max_length=16)),
                ("file_path", models.CharField(max_length=256)),
                ("file_name", models.CharField(max_length=128)),
                ("file_type", models.CharField(max_length=128)),
                ("n_lines_added", models.IntegerField(default=0)),
                ("n_lines_deleted", models.IntegerField(default=0)),
                ("n_lines_changed", models.IntegerField(default=0)),
                ("n_lines_of_code", models.IntegerField(default=0)),
                ("n_methods", models.IntegerField(default=0)),
                ("n_methods_changed", models.IntegerField(default=0)),
                ("is_on_exclude_list", models.BooleanField(default=False)),
                ("is_superfluous", models.BooleanField(default=False)),
                (
                    "commit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="files", to="indexer.commit"
                    ),
                ),
            ],
            options={
                "db_table": "committed_files",
            },
        ),
        migrations.AddField(
            model_name="commit",
            name="repos",
            field=models.ManyToManyField(through="indexer.RepositoryCommitLink", to="indexer.repository"),
        ),
    ]
