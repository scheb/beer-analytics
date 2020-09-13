from django.core.management.base import BaseCommand

from recipe_db.analytics import load_all_recipes, calculate_style_metric, calculate_style_recipe_count, \
    calculate_hop_recipe_count, calculate_hop_metric, load_all_recipe_hops
from recipe_db.models import Style, Hop

STYLE_METRICS = ['abv', 'ibu', 'ebc', 'original_plato', 'final_plato']
HOP_METRICS = ['alpha', 'amount_percent']


class Command(BaseCommand):
    help = "Calculate statistics on the recipes"

    def handle(self, *args, **options) -> None:
        recipes = load_all_recipes()

        self.stdout.write('Calculate style stats')
        for style in Style.objects.all():
            self.stdout.write('Style {}'.format(style.name))
            self.calculate_all_style_metrics(recipes, style)
            style.save()

        recipe_hops = load_all_recipe_hops()

        self.stdout.write('Calculate style stats')
        for hop in Hop.objects.all():
            self.stdout.write('Hop {}'.format(hop.name))
            self.calculate_all_hop_metrics(recipe_hops, hop)
            hop.save()

    def calculate_all_style_metrics(self, df, style: Style) -> None:
        style.recipes_count = calculate_style_recipe_count(df, style)

        for metric in STYLE_METRICS:
            self.stdout.write('Calculate {} for style {}'.format(metric, style.name))
            (min, mean, max) = calculate_style_metric(df, style, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(style, "recipes_%s_min" % metric, min)
            setattr(style, "recipes_%s_mean" % metric, mean)
            setattr(style, "recipes_%s_max" % metric, max)

    def calculate_all_hop_metrics(self, df, hop: Hop) -> None:
        hop.recipes_count = calculate_hop_recipe_count(df, hop)

        for metric in HOP_METRICS:
            self.stdout.write('Calculate {} for hop {}'.format(metric, hop.name))
            (min, mean, max) = calculate_hop_metric(df, hop, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(hop, "recipes_%s_min" % metric, min)
            setattr(hop, "recipes_%s_mean" % metric, mean)
            setattr(hop, "recipes_%s_max" % metric, max)
