# Generated by Django 4.2.6 on 2023-11-23 17:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipe_db", "0008_recipe_recipe_db_r_created_b37299_idx"),
    ]

    operations = [
        migrations.AddField(
            model_name="fermentable",
            name="search_popularity",
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="hop",
            name="search_popularity",
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="search_popularity",
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="tag",
            name="search_popularity",
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="yeast",
            name="search_popularity",
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
    ]