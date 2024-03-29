# Generated by Django 4.2.10 on 2024-03-02 13:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipe_db", "0014_style_color_style_conditioning_style_era_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SearchIndexUpdateQueue",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("operation", models.CharField(max_length=128)),
                ("index", models.CharField(max_length=64)),
                ("entity_id", models.CharField(max_length=64)),
                ("updated_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [models.Index(fields=["index", "updated_at"], name="recipe_db_s_index_93268d_idx")],
            },
        ),
    ]
