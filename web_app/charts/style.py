import abc
from typing import Optional

from recipe_db.analytics import get_style_hop_pairings, get_style_popular_fermentables, get_style_popular_hops, \
    get_style_metric_values, get_style_popularity
from recipe_db.models import Style, RecipeHop
from web_app.charts.utils import NoDataException
from web_app.plot import Plot, LinesChart, PreAggregatedBoxPlot, \
    PreAggregateHistogramChart, PreAggregatedPairsBoxPlot


class StyleChart:
    def __init__(self, style: Style, filter_param: Optional[str]) -> None:
        self.style = style
        self.filter_param = filter_param

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class StylePopularityChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_popularity(self.style)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        return LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes')


class StyleAbvChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'abv')
        if len(df) == 0:
            raise NoDataException()

        return PreAggregateHistogramChart().plot(df, 'abv', 'count')


class StyleIbuChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'ibu')
        if len(df) == 0:
            raise NoDataException()

        return PreAggregateHistogramChart().plot(df, 'ibu', 'count')


class StyleColorChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'srm')
        if len(df) == 0:
            raise NoDataException()

        return PreAggregateHistogramChart().plot(df, 'srm', 'count')


class StyleOGChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'og')
        if len(df) == 0:
            raise NoDataException()

        return PreAggregateHistogramChart().plot(df, 'og', 'count')


class StyleFGChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'fg')
        if len(df) == 0:
            raise NoDataException()

        return PreAggregateHistogramChart().plot(df, 'fg', 'count')


class StylePopularHopsChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_popular_hops(self.style, self.get_use_filter())
        if len(df) == 0:
            raise NoDataException()

        return PreAggregatedBoxPlot().plot(df, 'hop', 'amount_percent', 'Hops by Popularity', '% Amount')

    def get_use_filter(self):
        if self.filter_param == 'bittering':
            return [RecipeHop.MASH, RecipeHop.FIRST_WORT, RecipeHop.BOIL]
        if self.filter_param == 'aroma':
            return [RecipeHop.AROMA]
        if self.filter_param == 'dry-hop':
            return [RecipeHop.DRY_HOP]
        return []


class StylePopularFermentablesChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_popular_fermentables(self.style)
        if len(df) == 0:
            raise NoDataException()

        return PreAggregatedBoxPlot().plot(df, 'fermentable', 'amount_percent', 'Fermentables by Popularity', '% Amount')


class StyleHopPairingsChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_hop_pairings(self.style)
        if len(df) == 0:
            raise NoDataException()

        return PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'hop', 'amount_percent', None, '% Amount')


class StyleChartFactory:
    CHARTS = dict(
        popularity=StylePopularityChart,
        abv_histogram=StyleAbvChart,
        ibu_histogram=StyleIbuChart,
        color_histogram=StyleColorChart,
        og_histogram=StyleOGChart,
        fg_histogram=StyleFGChart,
        popular_hops=StylePopularHopsChart,
        popular_fermentables=StylePopularFermentablesChart,
        hop_pairings=StyleHopPairingsChart,
    )

    def get_chart(self, style: Style, chart_type: str, filter_param: Optional[str]) -> Plot:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(style, filter_param).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
