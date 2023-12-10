from typing import Iterable

import requests
from django.core.management.base import BaseCommand
from django.urls import reverse

from recipe_db.models import Hop, Fermentable, Yeast, Style
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.hop import HopChartFactory
from web_app.charts.style import StyleChartFactory
from web_app.charts.trend import TrendPeriod, TrendChartFactory
from web_app.charts.yeast import YeastChartFactory


BASE_URL = "https://www.beer-analytics.com"
WARMUP_PERCENTILE = 0.9
WARMUP_MOST_SEARCHED = 20

class Command(BaseCommand):
    help = "Warmup the cache for popular entities"

    def add_arguments(self, parser):
        parser.add_argument("--entities", "-e", nargs="+", type=str, help="Entities to recalculate")

    def handle(self, *args, **options) -> None:
        entities = options["entities"] or ["style", "hop", "fermentable", "yeast", "trend"]
        if "style" in entities:
            self.warmup_urls(self.get_warmup_urls_for_style())
        if "hop" in entities:
            self.warmup_urls(self.get_warmup_urls_for_hop())
        if "fermentable" in entities:
            self.warmup_urls(self.get_warmup_urls_for_fermentable())
        if "yeast" in entities:
            self.warmup_urls(self.get_warmup_urls_for_yeast())
        if "trend" in entities:
            self.warmup_urls(self.get_warmup_urls_for_trends())

    def get_warmup_urls_for_style(self) -> Iterable[str]:
        # Most popular styles by search
        styles = Style.get_most_searched(WARMUP_MOST_SEARCHED)
        yield from self.generate_style_urls(styles)

        # Largest datasets
        styles = Style.objects.filter(recipes_percentile__gt=WARMUP_PERCENTILE)
        yield from self.generate_style_urls(styles)

    def generate_style_urls(self, styles):
        for style in styles:
            chart_types = StyleChartFactory.get_types()
            for chart_type in chart_types:
                yield BASE_URL + reverse(
                    "style_chart_data",
                    kwargs=dict(
                        category_slug=style.category_slug,
                        slug=style.id,
                        chart_type=chart_type,
                    ),
                )

    def get_warmup_urls_for_hop(self) -> Iterable[str]:
        # Most popular hops by search
        hops = Hop.get_most_searched(WARMUP_MOST_SEARCHED)
        yield from self.generate_hop_urls(hops)

        # Largest datasets
        hops = Hop.objects.filter(recipes_percentile__gt=WARMUP_PERCENTILE)
        yield from self.generate_hop_urls(hops)

    def generate_hop_urls(self, hops) -> Iterable[str]:
        for hop in hops:
            chart_types = HopChartFactory.get_types()
            for chart_type in chart_types:
                yield BASE_URL + reverse(
                    "hop_chart_data",
                    kwargs=dict(
                        category_id=hop.category,
                        slug=hop.id,
                        chart_type=chart_type,
                    ),
                )

    def get_warmup_urls_for_fermentable(self) -> Iterable[str]:
        # Most popular fermentables by search
        fermentables = Fermentable.get_most_searched(WARMUP_MOST_SEARCHED)
        yield from self.generate_fermentable_urls(fermentables)

        # Largest datasets
        fermentables = Fermentable.objects.filter(recipes_percentile__gt=WARMUP_PERCENTILE)
        yield from self.generate_fermentable_urls(fermentables)

    def generate_fermentable_urls(self, fermentables) -> Iterable[str]:
        for fermentable in fermentables:
            chart_types = FermentableChartFactory.get_types()
            for chart_type in chart_types:
                yield BASE_URL + reverse(
                    "fermentable_chart_data",
                    kwargs=dict(
                        category_id=fermentable.category,
                        slug=fermentable.id,
                        chart_type=chart_type,
                    ),
                )

    def get_warmup_urls_for_yeast(self) -> Iterable[str]:
        # Most popular yeasts by search
        yeasts = Yeast.get_most_searched(WARMUP_MOST_SEARCHED)
        yield from self.generate_yeast_urls(yeasts)

        # Largest datasets
        yeasts = Yeast.objects.filter(recipes_percentile__gt=WARMUP_PERCENTILE)
        yield from self.generate_yeast_urls(yeasts)

    def generate_yeast_urls(self, yeasts) -> Iterable[str]:
        for yeast in yeasts:
            chart_types = YeastChartFactory.get_types()
            for chart_type in chart_types:
                yield BASE_URL + reverse(
                    "yeast_chart_data",
                    kwargs=dict(
                        type_id=yeast.type,
                        slug=yeast.id,
                        chart_type=chart_type,
                    ),
                )

    def get_warmup_urls_for_trends(self) -> Iterable[str]:
        for period in TrendPeriod:
            chart_types = TrendChartFactory.get_types()
            for chart_type in chart_types:
                yield BASE_URL + reverse(
                    "trend_chart_data",
                    kwargs=dict(
                        period=period.value,
                        chart_type=chart_type,
                    ),
                )

    def warmup_urls(self, urls: Iterable[str]):
        for url in urls:
            self.stdout.write(url)
            response = requests.get(url)
            self.stdout.write("%s sec." % response.elapsed.total_seconds())
