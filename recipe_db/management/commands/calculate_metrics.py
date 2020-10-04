import math

from django.core.management.base import BaseCommand

from recipe_db.analytics import load_all_recipes, calculate_style_metric, calculate_style_recipe_count, \
    calculate_hop_recipe_count, calculate_hop_metric, calculate_fermentable_recipe_count, \
    calculate_fermentable_metric, load_all_recipe_fermentables_aggregated, load_all_recipe_hops_aggregated, \
    get_hop_use_counts, get_style_percentiles, get_fermentables_percentiles, get_hops_percentiles, \
    get_yeasts_percentiles, load_all_recipe_yeasts_aggregated, calculate_yeast_recipe_count
from recipe_db.models import Style, Hop, Fermentable, Yeast

STYLE_METRICS = ['abv', 'ibu', 'ebc', 'srm', 'og', 'fg', 'original_plato', 'final_plato']
HOP_METRICS = ['alpha', 'amount_percent']
FERMENTABLE_METRICS = ['amount_percent', 'color_lovibond', 'color_ebc']


class Command(BaseCommand):
    help = "Calculate statistics on the recipes"

    def add_arguments(self, parser):
        parser.add_argument('--entities', '-e', nargs='+', type=str, help='Entities to recalculate')

    def handle(self, *args, **options) -> None:

        entities = options['entities'] or ['styles', 'hops', 'fermentables', 'yeasts']

        if 'styles' in entities:
            self.stdout.write('Calculate style stats')
            recipes = load_all_recipes()
            for style in Style.objects.all():
                self.stdout.write('Style {}'.format(style.name))
                self.calculate_all_style_metrics(recipes, style)
                style.save()

        if 'hops' in entities:
            recipe_hops = load_all_recipe_hops_aggregated()
            self.stdout.write('Calculate hop stats')
            for hop in Hop.objects.all():
                self.stdout.write('Hop {}'.format(hop.name))
                self.calculate_all_hop_metrics(recipe_hops, hop)
                hop.save()

        if 'fermentables' in entities:
            recipe_fermentables = load_all_recipe_fermentables_aggregated()
            self.stdout.write('Calculate fermentable stats')
            for fermentable in Fermentable.objects.all():
                self.stdout.write('Fermentable {}'.format(fermentable.name))
                self.calculate_all_fermentable_metrics(recipe_fermentables, fermentable)
                fermentable.save()

        if 'yeasts' in entities:
            recipe_yeasts = load_all_recipe_yeasts_aggregated()
            self.stdout.write('Calculate yeast stats')
            for yeast in Yeast.objects.all():
                self.stdout.write('Yeast {}'.format(yeast.name))
                self.calculate_all_yeast_metrics(recipe_yeasts, yeast)
                yeast.save()

        # Recalculate percentiles
        if 'styles' in entities:
            style_percentiles = get_style_percentiles()
            for style in Style.objects.all():
                self.stdout.write('Calculate percentile for style {}'.format(style.name))
                style.recipes_percentile = 0
                if style.id in style_percentiles:
                    style.recipes_percentile = style_percentiles[style.id]['percentile']
                    style.save()
                self.stdout.write(str(style.recipes_percentile))

        if 'hops' in entities:
            hop_percentiles = get_hops_percentiles()
            for hop in Hop.objects.all():
                self.stdout.write('Calculate percentile for hop {}'.format(hop.name))
                hop.recipes_percentile = 0
                if hop.id in hop_percentiles:
                    hop.recipes_percentile = hop_percentiles[hop.id]['percentile']
                    hop.save()
                self.stdout.write(str(hop.recipes_percentile))

        if 'fermentables' in entities:
            fermentable_percentiles = get_fermentables_percentiles()
            for fermentable in Fermentable.objects.all():
                self.stdout.write('Calculate percentile for fermentable {}'.format(fermentable.name))
                fermentable.recipes_percentile = 0
                if fermentable.id in fermentable_percentiles:
                    fermentable.recipes_percentile = fermentable_percentiles[fermentable.id]['percentile']
                    fermentable.save()
                self.stdout.write(str(fermentable.recipes_percentile))

        if 'yeasts' in entities:
            yeast_percentiles = get_yeasts_percentiles()
            for yeast in Yeast.objects.all():
                self.stdout.write('Calculate percentile for yeast {}'.format(yeast.name))
                yeast.recipes_percentile = 0
                if yeast.id in yeast_percentiles:
                    yeast.recipes_percentile = yeast_percentiles[yeast.id]['percentile']
                    yeast.save()
                self.stdout.write(str(yeast.recipes_percentile))

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

    def calculate_all_yeast_metrics(self, df, yeast: Yeast) -> None:
        yeast.recipes_count = calculate_yeast_recipe_count(df, yeast)
