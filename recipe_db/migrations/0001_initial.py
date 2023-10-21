# Generated by Django 4.2.6 on 2023-10-21 13:32

import datetime
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import recipe_db.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Fermentable",
            fields=[
                ("id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                (
                    "category",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("grain", "Grain"),
                            ("sugar", "Sugar"),
                            ("fruit", "Fruit"),
                            ("spice_herb", "Spices & Herbs"),
                            ("extract", "Malt Extract"),
                        ],
                        default=None,
                        max_length=32,
                        null=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("base", "Base Malt"),
                            ("cara_crystal", "Caramel/Crystal Malt"),
                            ("toasted", "Toasted"),
                            ("roasted", "Roasted"),
                            ("other_malt", "Other Malt"),
                            ("adjunct", "Adjunct Malt"),
                            ("unmalted_adjunct", "Unmalted Adjunct"),
                        ],
                        default=None,
                        max_length=32,
                        null=True,
                    ),
                ),
                ("alt_names", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("alt_names_extra", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("description", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("recipes_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_percentile", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_amount_percent_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_amount_percent_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_amount_percent_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_color_lovibond_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_color_lovibond_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_color_lovibond_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_color_ebc_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_color_ebc_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_color_ebc_max", models.FloatField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Hop",
            fields=[
                ("id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                (
                    "use",
                    models.CharField(
                        blank=True,
                        choices=[("aroma", "Aroma"), ("bittering", "Bittering"), ("dual-purpose", "Dual Purpose")],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                ("alt_names", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("alt_names_extra", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("origin", models.CharField(blank=True, default=None, max_length=32, null=True)),
                ("used_for", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("description", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("recipes_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_percentile", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_alpha_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_alpha_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_alpha_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_beta_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_beta_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_beta_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_amount_percent_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_amount_percent_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_amount_percent_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_use_mash_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_use_first_wort_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_use_boil_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_use_aroma_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_use_dry_hop_count", models.IntegerField(blank=True, default=None, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Recipe",
            fields=[
                ("uid", models.CharField(max_length=32, primary_key=True, serialize=False)),
                ("source", models.CharField(max_length=32)),
                ("source_id", models.CharField(max_length=32)),
                ("name", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("author", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "created",
                    models.DateField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(datetime.date(1990, 1, 1)),
                            django.core.validators.MaxValueValidator(recipe_db.models.get_tomorrow_date),
                        ],
                    ),
                ),
                ("style_raw", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "extract_efficiency",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "og",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0.95),
                            django.core.validators.MaxValueValidator(1.5),
                        ],
                    ),
                ),
                (
                    "fg",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0.95),
                            django.core.validators.MaxValueValidator(1.5),
                        ],
                    ),
                ),
                (
                    "original_plato",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "final_plato",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "abv",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "ebc",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "srm",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "ibu",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(5000),
                        ],
                    ),
                ),
                (
                    "mash_water",
                    models.IntegerField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "sparge_water",
                    models.IntegerField(
                        blank=True, default=None, null=True, validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                (
                    "boiling_time",
                    models.IntegerField(
                        blank=True, default=None, null=True, validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                (
                    "cast_out_wort",
                    models.IntegerField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RecipeFermentable",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind_raw", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("origin_raw", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "form",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("grain", "Grain"),
                            ("sugar", "Sugar"),
                            ("extract", "Extract"),
                            ("dry-extract", "Dry Extract"),
                            ("adjunct", "Adjunct"),
                        ],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "amount",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "amount_percent",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "color_lovibond",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "color_ebc",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "_yield",
                    models.FloatField(
                        blank=True,
                        db_column="yield",
                        default=None,
                        null=True,
                        validators=[recipe_db.models.GreaterThanValueValidator(0)],
                    ),
                ),
                (
                    "kind",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="recipe_db.fermentable",
                    ),
                ),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="recipe_db.recipe")),
            ],
        ),
        migrations.CreateModel(
            name="RecipeHop",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind_raw", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "form",
                    models.CharField(
                        blank=True,
                        choices=[("pellet", "Pellet"), ("plug", "Plug"), ("leaf", "Leaf")],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[("aroma", "Aroma"), ("bittering", "Bittering"), ("dual-purpose", "Dual-Purpose")],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "alpha",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "beta",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "use",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("mash", "Mash"),
                            ("first_wort", "First Wort"),
                            ("boil", "Boil"),
                            ("aroma", "Aroma"),
                            ("dry_hop", "Dry Hop"),
                        ],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "amount",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "amount_percent",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "time",
                    models.IntegerField(
                        blank=True, default=None, null=True, validators=[django.core.validators.MinValueValidator(0)]
                    ),
                ),
                (
                    "kind",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="recipe_db.hop",
                    ),
                ),
                ("recipe", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="recipe_db.recipe")),
            ],
        ),
        migrations.CreateModel(
            name="RecipeYeast",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind_raw", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("lab", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("product_id", models.CharField(blank=True, default=None, max_length=32, null=True)),
                (
                    "form",
                    models.CharField(
                        blank=True,
                        choices=[("liquid", "Liquid"), ("dry", "Dry"), ("slant", "Slant"), ("culture", "Culture")],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("ale", "Ale"),
                            ("lager", "Lager"),
                            ("wheat", "Wheat"),
                            ("wine", "Wine"),
                            ("champagne", "Champagne"),
                        ],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "amount",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "amount_percent",
                    models.FloatField(
                        blank=True,
                        default=None,
                        null=True,
                        validators=[
                            recipe_db.models.GreaterThanValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "min_attenuation",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "max_attenuation",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("category", models.CharField(blank=True, default=None, max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Yeast",
            fields=[
                ("id", models.CharField(max_length=255, primary_key=True, serialize=False)),
                ("product_id", models.CharField(blank=True, default=None, max_length=16, null=True)),
                ("alt_product_id", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("name", models.CharField(max_length=255)),
                ("alt_names", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("alt_names_extra", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("lab", models.CharField(max_length=255)),
                ("alt_lab", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("brand", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("alt_brand", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "form",
                    models.CharField(
                        blank=True,
                        choices=[("liquid", "Liquid"), ("dry", "Dry"), ("slant", "Slant"), ("culture", "Culture")],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("ale", "Ale"),
                            ("lager", "Lager"),
                            ("wheat", "Wheat"),
                            ("brett-bacteria", "Brett & Bacteria"),
                            ("wine-cider", "Wine & Cider"),
                        ],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "attenuation",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "min_temperature",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "max_temperature",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                (
                    "flocculation",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("low", "Low"),
                            ("medium-low", "Medium-Low"),
                            ("medium", "Medium"),
                            ("medium-high", "Medium-High"),
                            ("high", "High"),
                            ("very-high", "Very High"),
                        ],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "tolerance",
                    models.CharField(
                        blank=True,
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("very-high", "Very High")],
                        default=None,
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "tolerance_percent",
                    models.FloatField(
                        blank=True, default=None, null=True, validators=[recipe_db.models.GreaterThanValueValidator(0)]
                    ),
                ),
                ("description", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("recipes_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_percentile", models.FloatField(blank=True, default=None, null=True)),
            ],
            options={
                "unique_together": {("lab", "product_id")},
            },
        ),
        migrations.CreateModel(
            name="Style",
            fields=[
                ("id", models.CharField(max_length=4, primary_key=True, serialize=False)),
                ("slug", models.SlugField()),
                ("name", models.CharField(max_length=255)),
                ("alt_names", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("alt_names_extra", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("abv_min", models.FloatField(blank=True, default=None, null=True)),
                ("abv_max", models.FloatField(blank=True, default=None, null=True)),
                ("ibu_min", models.FloatField(blank=True, default=None, null=True)),
                ("ibu_max", models.FloatField(blank=True, default=None, null=True)),
                ("ebc_min", models.FloatField(blank=True, default=None, null=True)),
                ("ebc_max", models.FloatField(blank=True, default=None, null=True)),
                ("srm_min", models.FloatField(blank=True, default=None, null=True)),
                ("srm_max", models.FloatField(blank=True, default=None, null=True)),
                ("og_min", models.FloatField(blank=True, default=None, null=True)),
                ("og_max", models.FloatField(blank=True, default=None, null=True)),
                ("original_plato_min", models.FloatField(blank=True, default=None, null=True)),
                ("original_plato_max", models.FloatField(blank=True, default=None, null=True)),
                ("fg_min", models.FloatField(blank=True, default=None, null=True)),
                ("fg_max", models.FloatField(blank=True, default=None, null=True)),
                ("final_plato_min", models.FloatField(blank=True, default=None, null=True)),
                ("final_plato_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_count", models.IntegerField(blank=True, default=None, null=True)),
                ("recipes_percentile", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_abv_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_abv_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_abv_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_ibu_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_ibu_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_ibu_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_ebc_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_ebc_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_ebc_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_srm_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_srm_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_srm_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_og_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_og_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_og_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_original_plato_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_original_plato_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_original_plato_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_fg_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_fg_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_fg_max", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_final_plato_min", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_final_plato_mean", models.FloatField(blank=True, default=None, null=True)),
                ("recipes_final_plato_max", models.FloatField(blank=True, default=None, null=True)),
                ("strength", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("color", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("fermentation", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("conditioning", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("region_of_origin", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("family", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("specialty_beer", models.BooleanField(default=False)),
                ("era", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("bitter_balances", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("sour_hoppy_sweet", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("spice", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("smoke_roast", models.CharField(blank=True, default=None, max_length=255, null=True)),
                (
                    "parent_style",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="recipe_db.style",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RecipeYeastExtra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("value", models.TextField(blank=True, default=None, null=True)),
                ("yeast", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="recipe_db.recipeyeast")),
            ],
        ),
        migrations.AddField(
            model_name="recipeyeast",
            name="kind",
            field=models.ForeignKey(
                blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to="recipe_db.yeast"
            ),
        ),
        migrations.AddField(
            model_name="recipeyeast",
            name="recipe",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="recipe_db.recipe"),
        ),
        migrations.CreateModel(
            name="RecipeHopExtra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("value", models.TextField(blank=True, default=None, null=True)),
                ("hop", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="recipe_db.recipehop")),
            ],
        ),
        migrations.CreateModel(
            name="RecipeFermentableExtra",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(blank=True, default=None, max_length=255, null=True)),
                ("value", models.TextField(blank=True, default=None, null=True)),
                (
                    "fermentable",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="recipe_db.recipefermentable"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="recipe",
            name="associated_styles",
            field=models.ManyToManyField(related_name="all_recipes", to="recipe_db.style"),
        ),
        migrations.AddField(
            model_name="recipe",
            name="style",
            field=models.ForeignKey(
                blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to="recipe_db.style"
            ),
        ),
        migrations.AddField(
            model_name="hop",
            name="aroma_tags",
            field=models.ManyToManyField(to="recipe_db.tag"),
        ),
        migrations.AddField(
            model_name="hop",
            name="substitutes",
            field=models.ManyToManyField(to="recipe_db.hop"),
        ),
    ]
