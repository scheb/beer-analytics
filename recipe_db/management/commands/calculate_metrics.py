from django.core.management.base import BaseCommand

from recipe_db.analytics import load_all_recipes, calculate_style_metric, calculate_style_recipe_count
from recipe_db.models import Style


STYLE_METRICS = ['abv', 'ibu', 'ebc', 'original_plato', 'final_plato']


class Command(BaseCommand):
    help = "Calculate statistics on the recipes"

    def handle(self, *args, **options) -> None:
        df = load_all_recipes()

        self.stdout.write('Calculate style stats')
        for style in Style.objects.all():
            self.stdout.write('Style {}'.format(style.name))
            self.calculate_all_style_metrics(df, style)
            style.save()

    def calculate_all_style_metrics(self, df, style: Style) -> None:
        style.recipes_count = calculate_style_recipe_count(df, style)

        for metric in STYLE_METRICS:
            self.stdout.write('Calculate {} for style {}'.format(metric, style.name))
            (min, mean, max) = calculate_style_metric(df, style, metric)
            self.stdout.write(str((min, mean, max)))
            setattr(style, "recipes_%s_min" % metric, min)
            setattr(style, "recipes_%s_mean" % metric, mean)
            setattr(style, "recipes_%s_max" % metric, max)
