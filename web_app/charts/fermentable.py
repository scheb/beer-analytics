from abc import ABC

from recipe_db.analytics import get_fermentable_popularity, get_fermentable_common_styles_relative, \
    get_fermentable_common_styles_absolute, get_fermentable_metric_values, get_fermentable_amount_range, \
    get_fermentable_pairing_fermentables, get_fermentable_amount_range_per_style
from recipe_db.models import Fermentable
from web_app.charts.utils import NoDataException, Chart, ChartDefinition
from web_app.plot import LinesChart, BarChart, PreAggregateHistogramChart, RangeBoxPlot, \
    PreAggregatedPairsBoxPlot, PreAggregatedBoxPlot


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
        df = get_fermentable_metric_values(self.fermentable, 'color_lovibond')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'color_lovibond', 'count')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class FermentableAmountRangeChart(FermentableChart):
    CHART_TITLE = "Amount of <b>%s</b> fermentables used"
    IMAGE_ALT = "Amount of %s fermentables used in beer recipes"

    def plot(self) -> Chart:
        df = get_fermentable_amount_range(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = RangeBoxPlot().plot(df, 'amount_percent')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class FermentablePopularityChart(FermentableChart):
    CHART_TITLE = "Popularity of <b>%s</b> fermentables over time"
    IMAGE_ALT = "Popularity of the %s fermentables over time"

    def plot(self) -> Chart:
        df = get_fermentable_popularity(self.fermentable)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'fermentable', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class FermentableCommonStylesAbsoluteChart(FermentableChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> fermentables (by number of recipes)"
    IMAGE_ALT = "Typical beer styles using %s fermentables (by number of recipes)"

    def plot(self) -> Chart:
        df = get_fermentable_common_styles_absolute(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes', 'Style', 'Number Recipes')
        return Chart(figure, title=self.get_chart_title())


class FermentableCommonStylesRelativeChart(FermentableChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> fermentables (by percent of recipes)"
    IMAGE_ALT = "Typical beer styles using %s fermentables (by percent of recipes)"

    def plot(self) -> Chart:
        df = get_fermentable_common_styles_relative(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes_percent', 'Style', 'Used in % Recipes')
        return Chart(figure, title=self.get_chart_title())


class FermentableStyleAmountChart(FermentableChart):
    CHART_TITLE = "Amount of <b>%s</b> fermentables used per beer style"
    IMAGE_ALT = "Amount of %s fermentables used per beer style"

    def plot(self) -> Chart:
        df = get_fermentable_amount_range_per_style(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'style', 'amount_percent', 'Style', '% Amount')
        return Chart(figure, title=self.get_chart_title())


class FermentablePairingsChart(FermentableChart):
    CHART_TITLE = "Fermentables typically paired with <b>%s</b> fermentables"
    IMAGE_ALT = "Fermentables typically paired with the %s fermentable"

    def plot(self) -> Chart:
        df = get_fermentable_pairing_fermentables(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'fermentable', 'amount_percent', None, '% Amount')
        return Chart(figure, title=self.get_chart_title())


class FermentableChartFactory:
    CHARTS = dict(
        color_histogram=FermentableColorChart,
        amount_percent_range=FermentableAmountRangeChart,
        popularity=FermentablePopularityChart,
        typical_styles_absolute=FermentableCommonStylesAbsoluteChart,
        typical_styles_relative=FermentableCommonStylesRelativeChart,
        amount_used_per_style=FermentableStyleAmountChart,
        fermentable_pairings=FermentablePairingsChart,
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
        return chart_type.replace('-', '_')
