from django.core.management.base import BaseCommand

from recipe_db.analytics.metrics.hop import HopMetricCalculator
from recipe_db.models import Hop, HopPairing

HOP_MIN_RECIPES = 20

class Command(BaseCommand):
    help = "Calculate hop pairings"

    def handle(self, *args, **options) -> None:
        calculator = HopMetricCalculator()

        for hop in Hop.objects.all():
            hop.pairings.delete()  # Remove existing pairings
            if hop.recipes_count is None or hop.recipes_count < HOP_MIN_RECIPES:
                continue

            self.stdout.write("Calculate pairings for hop {}".format(hop.name))
            pairings = calculator.clac_pairings(hop)

            for kind_id, count in pairings.items():
                self.stdout.write("- Pairing: {} -> {} recipes".format(kind_id, count))
                paired_hop = Hop.objects.get(pk=kind_id)
                pairing = HopPairing(hop=hop, paired_hop=paired_hop, rank=count)
                pairing.save()
