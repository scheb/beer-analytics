from abc import ABC

from recipe_db.analytics.spotlight.fermentable import FermentableAnalysis
from recipe_db.models import Fermentable
from web_app.charts.utils import NoDataException, Chart, ChartDefinition
from web_app.meta import OPEN_GRAPH_IMAGE_WIDTH, OPEN_GRAPH_IMAGE_HEIGHT
from web_app.plot import LinesChart, BarChart, PreAggregateHistogramChart, RangeBoxPlot, PreAggregatedBoxPlot


class FermentableChart(ChartDefinition, ABC):
    CHART_TITLE = None
    IMAGE_ALT = None

    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

    def get_chart_title(self) -> str:
        return self.CHART_TITLE % self.fermentable.name

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT % self.fermentable.name


class FermentableColorChart(FermentableChart):
    CHART_TITLE = "Color of <b>%s</b> fermentables"
    IMAGE_ALT = "Histogram of the color (°Lovibond) of %s fermentables"

    def plot(self) -> Chart:
        df = FermentableAnalysis(self.fermentable).metric_histogram("color_lovibond")
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, "color_lovibond", "count")
        return Chart(figure, 500, 350, title=self.get_chart_title())


class FermentableAmountRangeChart(FermentableChart):
    CHART_TITLE = "Amount of <b>%s</b> fermentables used"
    IMAGE_ALT = "Amount of %s fermentables used in beer recipes"

    def plot(self) -> Chart:
        df = FermentableAnalysis(self.fermentable).amount_range()
        if len(df) == 0:
            raise NoDataException()

        figure = RangeBoxPlot().plot(df, "amount_percent")
        return Chart(figure, 500, 350, title=self.get_chart_title())


class FermentablePopularityChart(FermentableChart):
    CHART_TITLE = "Popularity of <b>%s</b> fermentables over time"
    IMAGE_ALT = "Popularity of the %s fermentables over time"

    def plot(self) -> Chart:
        df = FermentableAnalysis(self.fermentable).popularity()
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, "month", "recipes_percent", "fermentable", "Month/Year", "% of All Recipes")
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class FermentableCommonStylesAbsoluteChart(FermentableChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> fermentables (by number of recipes)"
    IMAGE_ALT = "Typical beer styles using %s fermentables (by number of recipes)"

    def plot(self) -> Chart:
        df = FermentableAnalysis(self.fermentable).common_styles_absolute()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, "beer_style", "recipes", None, "Total Number of Recipes")
        return Chart(figure, title=self.get_chart_title())


class FermentableCommonStylesRelativeChart(FermentableChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> fermentables (by percent of recipes)"
    IMAGE_ALT = "Typical beer styles using %s fermentables (by percent of recipes)"

    def plot(self) -> Chart:
        df = FermentableAnalysis(self.fermentable).common_styles_relative()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, "beer_style", "recipes_percent", None, "Used in % of the Style's Recipes")
        return Chart(figure, title=self.get_chart_title())


class FermentableStyleAmountChart(FermentableChart):
    CHART_TITLE = "Amount of <b>%s</b> fermentables used per beer style"
    IMAGE_ALT = "Amount of %s fermentables used per beer style"

    def plot(self) -> Chart:
        df = FermentableAnalysis(self.fermentable).amount_per_style()
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, "beer_style", "amount_percent", "Style", "% of Weight in Recipe")
        return Chart(figure, title=self.get_chart_title())


class FermentableOpenGraphChart(FermentablePopularityChart):
    def plot(self) -> Chart:
        chart = super().plot()
        chart.width = OPEN_GRAPH_IMAGE_WIDTH
        chart.height = OPEN_GRAPH_IMAGE_HEIGHT
        return chart


class FermentableChartFactory:
    CHARTS = dict(
        og=FermentableOpenGraphChart,
        color_histogram=FermentableColorChart,
        amount_percent_range=FermentableAmountRangeChart,
        popularity=FermentablePopularityChart,
        typical_styles_absolute=FermentableCommonStylesAbsoluteChart,
        typical_styles_relative=FermentableCommonStylesRelativeChart,
        amount_used_per_style=FermentableStyleAmountChart,
    )

    @classmethod
    def get_chart(cls, fermentable: Fermentable, chart_type: str) -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(fermentable)

    @classmethod
    def plot_chart(cls, fermentable: Fermentable, chart_type: str) -> Chart:
        return cls.get_chart(fermentable, chart_type).plot()

    @classmethod
    def is_supported_chart(cls, chart_type: str) -> bool:
        chart_type = cls.normalize_type(chart_type)
        return chart_type in cls.CHARTS

    @classmethod
    def normalize_type(cls, chart_type: str) -> str:
        return chart_type.replace("-", "_")

    @classmethod
    def urlize_type(cls, chart_type: str) -> str:
        return chart_type.replace("_", "-")

    @classmethod
    def get_types(cls):
        return list(cls.CHARTS.keys())
