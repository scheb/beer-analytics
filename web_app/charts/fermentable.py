import abc

from recipe_db.analytics import get_fermentable_popularity, get_fermentable_common_styles_relative, \
    get_fermentable_common_styles_absolute, get_fermentable_metric_values, get_fermentable_amount_range, \
    get_fermentable_pairing_fermentables, get_fermentable_amount_range_per_style
from recipe_db.models import Fermentable
from web_app.charts.utils import NoDataException, Chart
from web_app.plot import LinesChart, BarChart, PreAggregateHistogramChart, RangeBoxPlot, \
    PreAggregatedPairsBoxPlot, PreAggregatedBoxPlot


class FermentableChart:
    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class FermentablePopularityChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_popularity(self.fermentable)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'fermentable', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT*0.66, title="Popularity of <b>%s</b> fermentables over time" % self.fermentable.name)


class FermentableColorChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_metric_values(self.fermentable, 'color_lovibond')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'color_lovibond', 'count')
        return Chart(figure, 500, 350, title="Color of <b>%s</b> fermentables" % self.fermentable.name)


class FermentableAmountRangeChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_amount_range(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = RangeBoxPlot().plot(df, 'amount_percent')
        return Chart(figure, 500, 350, title="Amount of <b>%s</b> fermentables used" % self.fermentable.name)


class FermentableCommonStylesAbsoluteChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_common_styles_absolute(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes', 'Style', 'Number Recipes')
        return Chart(figure, title="Typical beer styles using <b>%s</b> fermentables (by number of recipes)" % self.fermentable.name)


class FermentableCommonStylesRelativeChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_common_styles_relative(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes_percent', 'Style', 'Used in % Recipes')
        return Chart(figure, title="Typical beer styles using <b>%s</b> fermentables (by percent of recipes)" % self.fermentable.name)


class FermentableStyleAmountChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_amount_range_per_style(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'style', 'amount_percent', 'Style', '% Amount')
        return Chart(figure, title="Amount of <b>%s</b> fermentables used per beer style" % self.fermentable.name)


class FermentablePairingsChart(FermentableChart):
    def plot(self) -> Chart:
        df = get_fermentable_pairing_fermentables(self.fermentable)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'fermentable', 'amount_percent', None, '% Amount')
        return Chart(figure, title="Fermentables typically paired with <b>%s</b> fermentables" % self.fermentable.name)


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

    def get_chart(self, fermentable: Fermentable, chart_type: str) -> Chart:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(fermentable).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
