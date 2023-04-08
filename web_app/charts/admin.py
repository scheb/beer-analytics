from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Optional

from recipe_db.analytics.recipe import RecipesPopularityAnalysis, RecipesTrendAnalysis
from recipe_db.analytics.scope import RecipeScope, HopProjection, YeastProjection
from recipe_db.analytics.spotlight.hop import HOP_FILTER_TO_USES
from recipe_db.analytics.spotlight.yeast import YEAST_FILTER_TO_TYPES
from web_app.charts.utils import Chart, ChartDefinition, NoDataException
from web_app.plot import LinesChart


class InfluxSourceChart(ChartDefinition, ABC):
    CHART_TITLE = "Influx by Source"
    IMAGE_ALT = "Influx by Source"

    def __init__(self, filter_param: Optional[str]) -> None:
        self.filter_param = filter_param

    def get_chart_title(self) -> str:
        return self.CHART_TITLE

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT

    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        df = analysis.popularity_per_source(top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(
            df, "month", "recipes_number", "source", "Month/Year", "Number Recipes"
        )
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())

class AdminChartFactory:
    CHARTS = dict(
        influx_source=InfluxSourceChart,
    )

    @classmethod
    def get_chart(cls, chart_type: str, filter_param: Optional[str] = "") -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(filter_param)

    @classmethod
    def plot_chart(cls, chart_type: str, filter_param: Optional[str] = "") -> Chart:
        return cls.get_chart(chart_type, filter_param).plot()

    @classmethod
    def is_supported_chart(cls, chart_type: str) -> bool:
        chart_type = cls.normalize_type(chart_type)
        return chart_type in cls.CHARTS

    @classmethod
    def normalize_type(cls, chart_type: str) -> str:
        return chart_type.replace("-", "_")

    @classmethod
    def get_types(cls):
        return list(cls.CHARTS.keys())
