# Generated by Django 4.2.9 on 2024-01-28 17:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipe_db", "0013_recipe_style_oor"),
    ]

    operations = [
        migrations.AddField(
            model_name="style",
            name="color",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="conditioning",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="era",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="fermentation",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="flavor",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="origin",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="style",
            name="strength",
            field=models.CharField(blank=True, default=None, max_length=16, null=True),
        ),
    ]
