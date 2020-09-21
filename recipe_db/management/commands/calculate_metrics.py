import math

from django.core.management.base import BaseCommand

from recipe_db.analytics import load_all_recipes, calculate_style_metric, calculate_style_recipe_count, \
    calculate_hop_recipe_count, calculate_hop_metric, calculate_fermentable_recipe_count, \
    calculate_fermentable_metric, load_all_recipe_fermentables_aggregated, load_all_recipe_hops_aggregated, \
    get_hop_use_counts
from recipe_db.models import Style, Hop, Fermentable

STYLE_METRICS = ['abv', 'ibu', 'ebc', 'srm', 'og', 'fg', 'original_plato', 'final_plato']
HOP_METRICS = ['alpha', 'amount_percent']
FERMENTABLE_METRICS = ['amount_percent', 'color_lovibond', 'color_ebc']


class Command(BaseCommand):
    help = "Calculate statistics on the recipes"

    def handle(self, *args, **options) -> None:
        recipes = load_all_recipes()

        self.stdout.write('Calculate style stats')
        for style in Style.objects.all():
            self.stdout.write('Style {}'.format(style.name))
            self.calculate_all_style_metrics(recipes, style)
            style.save()

        recipe_hops = load_all_recipe_hops_aggregated()

        self.stdout.write('Calculate hop stats')
        for hop in Hop.objects.all():
            self.stdout.write('Hop {}'.format(hop.name))
            self.calculate_all_hop_metrics(recipe_hops, hop)
            hop.save()

        recipe_fermentables = load_all_recipe_fermentables_aggregated()

        self.stdout.write('Calculate fermentable stats')
        for fermentable in Fermentable.objects.all():
            self.stdout.write('Fermentable {}'.format(fermentable.name))
            self.calculate_all_fermentable_metrics(recipe_fermentables, fermentable)
            fermentable.save()

    def calculate_all_style_metrics(self, df, style: Style) -> None:
        style.recipes_count = calculate_style_recipe_count(df, style)

        for metric in STYLE_METRICS:
            self.stdout.write('Calculate {} for style {}'.format(metric, style.name))
            (min, mean, max) = calculate_style_metric(df, style, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(style, "recipes_%s_min" % metric, None if math.isnan(min) else min)
            setattr(style, "recipes_%s_mean" % metric, None if math.isnan(mean) else mean)
            setattr(style, "recipes_%s_max" % metric, None if math.isnan(max) else max)

    def calculate_all_hop_metrics(self, df, hop: Hop) -> None:
        hop.recipes_count = calculate_hop_recipe_count(df, hop)

        use_counts = get_hop_use_counts(hop)
        for use in use_counts:
            setattr(hop, 'recipes_use_%s_count' % use, use_counts[use])

        for metric in HOP_METRICS:
            self.stdout.write('Calculate {} for hop {}'.format(metric, hop.name))
            (min, mean, max) = calculate_hop_metric(df, hop, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(hop, "recipes_%s_min" % metric, None if math.isnan(min) else min)
            setattr(hop, "recipes_%s_mean" % metric, None if math.isnan(mean) else mean)
            setattr(hop, "recipes_%s_max" % metric, None if math.isnan(max) else max)

    def calculate_all_fermentable_metrics(self, df, fermentable: Fermentable) -> None:
        fermentable.recipes_count = calculate_fermentable_recipe_count(df, fermentable)

        for metric in FERMENTABLE_METRICS:
            self.stdout.write('Calculate {} for fermentable {}'.format(metric, fermentable.name))
            (min, mean, max) = calculate_fermentable_metric(df, fermentable, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(fermentable, "recipes_%s_min" % metric, None if math.isnan(min) else min)
            setattr(fermentable, "recipes_%s_mean" % metric, None if math.isnan(mean) else mean)
            setattr(fermentable, "recipes_%s_max" % metric, None if math.isnan(max) else max)
