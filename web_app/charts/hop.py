import abc

from recipe_db.analytics import get_hop_popularity, get_hop_common_styles_relative, get_hop_pairing_hops, \
    get_hop_common_styles_absolute, get_hop_metric_values, get_hop_amount_range, get_hop_usage, \
    get_hop_amount_range_per_style, get_hop_amount_range_per_use
from recipe_db.models import Hop
from web_app.charts.utils import NoDataException, Chart
from web_app.plot import LinesChart, BarChart, PreAggregatedPairsBoxPlot, PreAggregateHistogramChart, \
    RangeBoxPlot, PreAggregatedBoxPlot


class HopChart:
    def __init__(self, hop: Hop) -> None:
        self.hop = hop

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class HopPopularityChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_popularity(self.hop)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT*0.66, title="Popularity of <b>%s</b> hops over time" % self.hop.name)


class HopAlphaChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_metric_values(self.hop, 'alpha')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'alpha', 'count')
        return Chart(figure, 500, 350, title="Alpha acid of <b>%s</b> hops" % self.hop.name)


class HopAmountRangeChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_amount_range(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = RangeBoxPlot().plot(df, 'amount_percent')
        return Chart(figure, 500, 350, title="Amount of <b>%s</b> hops used" % self.hop.name)


class HopUsageChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_usage(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart(add_margin=False).plot(df, 'use', 'recipes', None, None)
        return Chart(figure, 500, 350, title="How <b>%s</b> hops are used" % self.hop.name)


class HopCommonStylesAbsoluteChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_common_styles_absolute(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes', 'Style', 'Number Recipes')
        return Chart(figure, title="Typical beer styles using <b>%s</b> hops (by number of recipes)" % self.hop.name)


class HopCommonStylesRelativeChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_common_styles_relative(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes_percent', 'Style', 'Used in % Recipes')
        return Chart(figure, title="Typical beer styles using <b>%s</b> hops (by percent of recipes)" % self.hop.name)


class HopStyleAmountChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_amount_range_per_style(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'style', 'amount_percent', 'Style', '% Amount')
        return Chart(figure, title="Amount of <b>%s</b> hops used per beer style" % self.hop.name)


class HopUsageAmountChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_amount_range_per_use(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'use', 'amount_percent', 'Usage', '% Amount')
        return Chart(figure, title="Amount of <b>%s</b> hops per on usage type" % self.hop.name)


class HopPairingsChart(HopChart):
    def plot(self) -> Chart:
        df = get_hop_pairing_hops(self.hop)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'hop', 'amount_percent', None, '% Amount')
        return Chart(figure, title="Hops typically paired with <b>%s</b> hops" % self.hop.name)


class HopChartFactory:
    CHARTS = dict(
        alpha_histogram=HopAlphaChart,
        amount_percent_range=HopAmountRangeChart,
        usage_types=HopUsageChart,
        popularity=HopPopularityChart,
        typical_styles_absolute=HopCommonStylesAbsoluteChart,
        typical_styles_relative=HopCommonStylesRelativeChart,
        amount_used_per_style=HopStyleAmountChart,
        amount_used_per_use=HopUsageAmountChart,
        hop_pairings=HopPairingsChart,
    )

    def get_chart(self, hop: Hop, chart_type: str) -> Chart:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(hop).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
