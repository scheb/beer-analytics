# Generated by Django 4.2.6 on 2024-01-20 18:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipe_db", "0011_bjcp2021"),
    ]

    operations = [
        migrations.AddField(
            model_name="style",
            name="bjcp_url",
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
    ]
