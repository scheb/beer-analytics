from abc import ABC

from recipe_db.analytics.spotlight.hop import HopAnalysis
from recipe_db.models import Hop
from web_app.charts.utils import NoDataException, Chart, ChartDefinition
from web_app.meta import OPEN_GRAPH_IMAGE_WIDTH, OPEN_GRAPH_IMAGE_HEIGHT
from web_app.plot import (
    LinesChart,
    BarChart,
    PreAggregatedPairsBoxPlot,
    PreAggregateHistogramChart,
    RangeBoxPlot,
    PreAggregatedBoxPlot,
)


class HopChart(ChartDefinition, ABC):
    CHART_TITLE = None
    IMAGE_ALT = None

    def __init__(self, hop: Hop) -> None:
        self.hop = hop

    def get_chart_title(self) -> str:
        return self.CHART_TITLE % self.hop.name

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT % self.hop.name


class HopAlphaChart(HopChart):
    CHART_TITLE = "Alpha acid of <b>%s</b> hops"
    IMAGE_ALT = "Histogram of alpha acid in %s hops"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).metric_histogram("alpha")
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, "alpha", "count")
        return Chart(figure, 500, 350, title=self.get_chart_title())


class HopBetaChart(HopChart):
    CHART_TITLE = "Beta acid of <b>%s</b> hops"
    IMAGE_ALT = "Histogram of beta acid in %s hops"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).metric_histogram("beta")
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, "beta", "count")
        return Chart(figure, 500, 350, title=self.get_chart_title())


class HopAmountRangeChart(HopChart):
    CHART_TITLE = "Amount of <b>%s</b> hops used"
    IMAGE_ALT = "How %s hops are typically used in beer recipes"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).amount_range()
        if len(df) == 0:
            raise NoDataException()

        figure = RangeBoxPlot().plot(df, "amount_percent")
        return Chart(figure, 500, 350, title=self.get_chart_title())


class HopUsageChart(HopChart):
    CHART_TITLE = "How <b>%s</b> hops are used"
    IMAGE_ALT = "Amount of %s hops used per beer style"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).usages()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart(add_margin=False).plot(df, "use", "recipes", None, None)
        return Chart(figure, 500, 350, title=self.get_chart_title())


class HopPopularityChart(HopChart):
    CHART_TITLE = "Popularity of <b>%s</b> hops over time"
    IMAGE_ALT = "Popularity of the %s hop over time"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).popularity()
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, "month", "recipes_percent", "hop", "Month/Year", "% of All Recipes")
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class HopCommonStylesAbsoluteChart(HopChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> hops (by number of recipes)"
    IMAGE_ALT = "Typical beer styles using %s hops (by number of recipes)"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).common_styles_absolute()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, "beer_style", "recipes", None, "Total Number of Recipes")
        return Chart(figure, title=self.get_chart_title())


class HopCommonStylesRelativeChart(HopChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> hops (by percent of recipes)"
    IMAGE_ALT = "Typical beer styles using %s hops (by percent of recipes)"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).common_styles_relative()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, "beer_style", "recipes_percent", None, "Used in % of the Style's Recipes")
        return Chart(figure, title=self.get_chart_title())


class HopStyleAmountChart(HopChart):
    CHART_TITLE = "Amount of <b>%s</b> hops used per beer style"
    IMAGE_ALT = "Amount of %s hops per on usage type"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).amount_per_style()
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, "beer_style", "amount_percent", None, "% of Weight in Recipe")
        return Chart(figure, title=self.get_chart_title())


class HopUsageAmountChart(HopChart):
    CHART_TITLE = "Amount of <b>%s</b> hops per on usage type"
    IMAGE_ALT = "Amount of %s hops per on usage type"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).amount_per_use()
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, "use", "amount_percent", "Usage", "% of Weight in Recipe")
        return Chart(figure, title=self.get_chart_title())


class HopPairingsChart(HopChart):
    CHART_TITLE = "Hops typically paired with <b>%s</b> hops"
    IMAGE_ALT = "Hops typically paired with %s hops"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).pairings()
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, "pairing", "hop", "amount_percent", None, "% of Weight in Recipe")
        return Chart(figure, title=self.get_chart_title())


class HopTrendingYeastsChart(HopChart):
    CHART_TITLE = "Trending yeasts combined with <b>%s</b> hops"
    IMAGE_ALT = "Trending yeasts combined with %s hops"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).trending_yeasts()
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, "month", "recipes_percent", "yeast", None, "% of Recipes")
        return Chart(figure, title=self.get_chart_title())


class HopPopularYeastsChart(HopChart):
    CHART_TITLE = "Popular yeasts combined with <b>%s</b> hops"
    IMAGE_ALT = "Popular yeasts combined with %s hops"

    def plot(self) -> Chart:
        df = HopAnalysis(self.hop).popular_yeasts()
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, "month", "recipes_percent", "yeast", None, "% of Recipes")
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class HopOpenGraphChart(HopPopularityChart):
    def plot(self) -> Chart:
        chart = super().plot()
        chart.width = OPEN_GRAPH_IMAGE_WIDTH
        chart.height = OPEN_GRAPH_IMAGE_HEIGHT
        return chart


class HopChartFactory:
    CHARTS = dict(
        og=HopOpenGraphChart,
        alpha_histogram=HopAlphaChart,
        beta_histogram=HopBetaChart,
        amount_percent_range=HopAmountRangeChart,
        usage_types=HopUsageChart,
        popularity=HopPopularityChart,
        typical_styles_absolute=HopCommonStylesAbsoluteChart,
        typical_styles_relative=HopCommonStylesRelativeChart,
        amount_used_per_style=HopStyleAmountChart,
        amount_used_per_use=HopUsageAmountChart,
        hop_pairings=HopPairingsChart,
        popular_yeasts=HopPopularYeastsChart,
        trending_yeasts=HopTrendingYeastsChart,
    )

    @classmethod
    def get_chart(cls, hop: Hop, chart_type: str) -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(hop)

    @classmethod
    def plot_chart(cls, hop: Hop, chart_type: str) -> Chart:
        return cls.get_chart(hop, chart_type).plot()

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
