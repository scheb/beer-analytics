from django.core.management.base import BaseCommand

from recipe_db.analytics.metrics.hop import HopMetricCalculator
from recipe_db.models import Hop

HOP_MIN_RECIPES = 20

class Command(BaseCommand):
    help = "Calculate hop pairings"

    def handle(self, *args, **options) -> None:
        calculator = HopMetricCalculator()

        for hop in Hop.objects.all():
            hop.pairings.clear()  # Clear existing pairings
            if hop.recipes_count < HOP_MIN_RECIPES:
                continue

            self.stdout.write("Calculate pairings for hop {}".format(hop.name))
            pairings = calculator.clac_pairings(hop)

            for kind_id, count in pairings.items():
                if count < (hop.recipes_count / 20):  # At least 5% of recipes
                    break  # Sorted by count, so we can stop here

                self.stdout.write("- Pairing: {} -> {} recipes".format(kind_id, count))
                hop.pairings.add(kind_id)
