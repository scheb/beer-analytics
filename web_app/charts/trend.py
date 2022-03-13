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


class TrendChart(ChartDefinition, ABC):
    CHART_TITLE = None
    IMAGE_ALT = None

    def __init__(self, period: TrendPeriod, filter_param: Optional[str]) -> None:
        self.period_months = period.months
        self.filter_param = filter_param

    def get_chart_title(self) -> str:
        return self.CHART_TITLE % self.period_months

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT % self.period_months


class TrendingHopsChart(TrendChart):
    CHART_TITLE = "<b>Trending hops</b> of the last %s months"
    IMAGE_ALT = "Trending hops of the last %s months"

    def plot(self) -> Chart:
        projection = HopProjection()
        if self.filter_param in HOP_FILTER_TO_USES:
            projection.uses = HOP_FILTER_TO_USES[self.filter_param]

        analysis = RecipesTrendAnalysis(RecipeScope())
        df = analysis.trending_hops(projection, trend_window_months=self.period_months)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, "month", "recipes_percent", "hop", None, "% of All Recipes")
        return Chart(figure, title=self.get_chart_title())


class PopularHopsChart(TrendChart):
    CHART_TITLE = "<b>Popular hops</b> of the last %s months"
    IMAGE_ALT = "Popular hops of the last %s months"

    def plot(self) -> Chart:
        projection = HopProjection()
        if self.filter_param in HOP_FILTER_TO_USES:
            projection.uses = HOP_FILTER_TO_USES[self.filter_param]

        analysis = RecipesPopularityAnalysis(RecipeScope())
        df = analysis.popularity_per_hop(projection, num_top=8, top_months=self.period_months)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(
            df, "month", "recipes_percent", "hop", "Month/Year", "% of All Recipes"
        )
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingYeastsChart(TrendChart):
    CHART_TITLE = "<b>Trending yeasts</b> of the last %s months"
    IMAGE_ALT = "Trending yeasts of the last %s months"

    def plot(self) -> Chart:
        projection = YeastProjection()
        if self.filter_param in YEAST_FILTER_TO_TYPES:
            projection.types = YEAST_FILTER_TO_TYPES[self.filter_param]

        analysis = RecipesTrendAnalysis(RecipeScope())
        df = analysis.trending_yeasts(projection, trend_window_months=self.period_months)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, "month", "recipes_percent", "yeast", None, "% of All Recipes")
        return Chart(figure, title=self.get_chart_title())


class PopularYeastsChart(TrendChart):
    CHART_TITLE = "<b>Popular yeasts</b> of the last %s months"
    IMAGE_ALT = "Popular yeasts of the last %s months"

    def plot(self) -> Chart:
        projection = YeastProjection()
        if self.filter_param in YEAST_FILTER_TO_TYPES:
            projection.types = YEAST_FILTER_TO_TYPES[self.filter_param]

        analysis = RecipesPopularityAnalysis(RecipeScope())
        df = analysis.popularity_per_yeast(projection, num_top=8, top_months=self.period_months)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(
            df, "month", "recipes_percent", "yeast", "Month/Year", "% of All Recipes"
        )
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingStylesChart(TrendChart):
    CHART_TITLE = "<b>Trending beer styles</b> of the last %s months"
    IMAGE_ALT = "Trending beer styles of the last %s months"

    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(RecipeScope())
        df = analysis.trending_styles(trend_window_months=self.period_months)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(
            df, "month", "recipes_percent", "beer_style", None, "% of All Recipes"
        )
        return Chart(figure, title=self.get_chart_title())


class PopularStylesChart(TrendChart):
    CHART_TITLE = "<b>Popular beer styles</b> of the last %s months"
    IMAGE_ALT = "Popular beer styles of the last %s months"

    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        df = analysis.popularity_per_style(num_top=8, top_months=self.period_months)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(
            df, "month", "recipes_percent", "beer_style", "Month/Year", "% of All Recipes"
        )
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendPeriod(Enum):
    SEASONAL = "seasonal"
    RECENT = "recent"

    @classmethod
    def from_string(cls, period: str) -> TrendPeriod:
        if period == "recent":
            return cls.RECENT
        elif period == "seasonal":
            return cls.SEASONAL
        raise ValueError('"%s" cannot be converted to TrendPeriod.' % period)

    @property
    def months(self) -> int:
        if self.value == self.SEASONAL.value:
            return 6
        if self.value == self.RECENT.value:
            return 24
        raise ValueError('Could not determine months value for TrendPeriod "%s"' % self.value)

    def __str__(self) -> str:
        return self.value


class TrendChartFactory:
    CHARTS = dict(
        trending_hops=TrendingHopsChart,
        trending_yeasts=TrendingYeastsChart,
        trending_styles=TrendingStylesChart,
        popular_hops=PopularHopsChart,
        popular_yeasts=PopularYeastsChart,
        popular_styles=PopularStylesChart,
    )

    @classmethod
    def get_chart(cls, chart_type: str, period: TrendPeriod, filter_param: Optional[str] = "") -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(period, filter_param)

    @classmethod
    def plot_chart(cls, chart_type: str, period: TrendPeriod, filter_param: Optional[str] = "") -> Chart:
        return cls.get_chart(chart_type, period, filter_param).plot()

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
