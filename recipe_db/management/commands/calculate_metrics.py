import math

from django.core.management.base import BaseCommand

from recipe_db.analytics.metrics.fermentable import FermentableMetricCalculator
from recipe_db.analytics.metrics.hop import HopMetricCalculator
from recipe_db.analytics.metrics.style import StyleMetricCalculator
from recipe_db.analytics.metrics.yeast import YeastMetricCalculator
from recipe_db.models import Style, Hop, Fermentable, Yeast


class Command(BaseCommand):
    help = "Calculate statistics on the recipes"

    def add_arguments(self, parser):
        parser.add_argument('--entities', '-e', nargs='+', type=str, help='Entities to recalculate')

    def handle(self, *args, **options) -> None:
        entities = options['entities'] or ['style', 'hop', 'fermentable', 'yeast']
        if 'style' in entities:
            self.calculate_for_style()
        if 'hop' in entities:
            self.calculate_for_hop()
        if 'fermentable' in entities:
            self.calculate_for_fermentable()
        if 'yeast' in entities:
            self.calculate_for_yeast()

    def calculate_for_style(self):
        self.stdout.write('Calculate style stats')
        calculator = StyleMetricCalculator()
        for style in Style.objects.all():
            self.stdout.write('Style {}'.format(style.name))
            self.calculate_all_style_metrics(calculator, style)
            style.save()

        style_percentiles = calculator.calc_percentiles()
        for style in Style.objects.all():
            self.stdout.write('Calculate percentile for style {}'.format(style.name))
            style.recipes_percentile = style_percentiles.get(style.id, 0)
            style.save()
            self.stdout.write(str(style.recipes_percentile))

    def calculate_for_hop(self):
        self.stdout.write('Calculate hop stats')
        calculator = HopMetricCalculator()
        for hop in Hop.objects.all():
            self.stdout.write('Hop {}'.format(hop.name))
            self.calculate_all_hop_metrics(calculator, hop)
            hop.save()

        hop_percentiles = calculator.calc_percentiles()
        for hop in Hop.objects.all():
            self.stdout.write('Calculate percentile for hop {}'.format(hop.name))
            hop.recipes_percentile = hop_percentiles.get(hop.id, 0)
            hop.save()
            self.stdout.write(str(hop.recipes_percentile))

    def calculate_for_fermentable(self):
        self.stdout.write('Calculate fermentable stats')
        calculator = FermentableMetricCalculator()
        for fermentable in Fermentable.objects.all():
            self.stdout.write('Fermentable {}'.format(fermentable.name))
            self.calculate_all_fermentable_metrics(calculator, fermentable)
            fermentable.save()

        fermentable_percentiles = calculator.calc_percentiles()
        for fermentable in Fermentable.objects.all():
            self.stdout.write('Calculate percentile for fermentable {}'.format(fermentable.name))
            fermentable.recipes_percentile = fermentable_percentiles.get(fermentable.id, 0)
            fermentable.save()
            self.stdout.write(str(fermentable.recipes_percentile))

    def calculate_for_yeast(self):
        self.stdout.write('Calculate yeast stats')
        calculator = YeastMetricCalculator()
        for yeast in Yeast.objects.all():
            self.stdout.write('Yeast {}'.format(yeast.name))
            self.calculate_all_yeast_metrics(calculator, yeast)
            yeast.save()

        yeast_percentiles = calculator.calc_percentiles()
        for yeast in Yeast.objects.all():
            self.stdout.write('Calculate percentile for yeast {}'.format(yeast.name))
            yeast.recipes_percentile = yeast_percentiles.get(yeast.id, 0)
            yeast.save()
            self.stdout.write(str(yeast.recipes_percentile))

    def calculate_all_style_metrics(self, calculator: StyleMetricCalculator, style: Style) -> None:
        style.recipes_count = calculator.calc_recipes_count(style)

        for metric in calculator.available_metrics:
            self.stdout.write('Calculate {} for style {}'.format(metric.value, style.name))
            (min, mean, max) = calculator.calc_metric(style, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(style, "recipes_%s_min" % metric.value, None if math.isnan(min) else min)
            setattr(style, "recipes_%s_mean" % metric.value, None if math.isnan(mean) else mean)
            setattr(style, "recipes_%s_max" % metric.value, None if math.isnan(max) else max)

    def calculate_all_hop_metrics(self, calculator: HopMetricCalculator, hop: Hop) -> None:
        hop.recipes_count = calculator.calc_recipes_count(hop)

        use_counts = calculator.calc_hop_use_counts(hop)
        for use in use_counts:
            setattr(hop, 'recipes_use_%s_count' % use, use_counts[use])

        for metric in calculator.available_metrics:
            self.stdout.write('Calculate {} for hop {}'.format(metric.value, hop.name))
            (min, mean, max) = calculator.calc_metric(hop, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(hop, "recipes_%s_min" % metric.value, None if math.isnan(min) else min)
            setattr(hop, "recipes_%s_mean" % metric.value, None if math.isnan(mean) else mean)
            setattr(hop, "recipes_%s_max" % metric.value, None if math.isnan(max) else max)

    def calculate_all_fermentable_metrics(self, calculator: FermentableMetricCalculator, fermentable: Fermentable) -> None:
        fermentable.recipes_count = calculator.calc_recipes_count(fermentable)

        for metric in calculator.available_metrics:
            self.stdout.write('Calculate {} for fermentable {}'.format(metric.value, fermentable.name))
            (min, mean, max) = calculator.calc_metric(fermentable, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(fermentable, "recipes_%s_min" % metric.value, None if math.isnan(min) else min)
            setattr(fermentable, "recipes_%s_mean" % metric.value, None if math.isnan(mean) else mean)
            setattr(fermentable, "recipes_%s_max" % metric.value, None if math.isnan(max) else max)

    def calculate_all_yeast_metrics(self, calculator: YeastMetricCalculator, yeast: Yeast) -> None:
        yeast.recipes_count = calculator.get_recipes_count(yeast)
