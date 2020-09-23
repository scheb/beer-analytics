import abc
from typing import Optional, Tuple

from recipe_db.analytics import get_style_hop_pairings, get_style_popular_fermentables, get_style_popular_hops, \
    get_style_metric_values, get_style_popularity
from recipe_db.models import Style, RecipeHop, Fermentable
from web_app.charts.utils import NoDataException, Chart
from web_app.plot import LinesChart, PreAggregatedBoxPlot, \
    PreAggregateHistogramChart, PreAggregatedPairsBoxPlot


class StyleChart:
    def __init__(self, style: Style, filter_param: Optional[str]) -> None:
        self.style = style
        self.filter_param = filter_param

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class StylePopularityChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_popularity(self.style)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes')
        return Chart(figure)


class StyleAbvChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_metric_values(self.style, 'abv')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'abv', 'count')
        return Chart(figure, 300, 200)


class StyleIbuChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_metric_values(self.style, 'ibu')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'ibu', 'count')
        return Chart(figure, 300, 200)


class StyleColorChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_metric_values(self.style, 'srm')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'srm', 'count')
        return Chart(figure, 300, 200)


class StyleOGChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_metric_values(self.style, 'og')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'og', 'count')
        return Chart(figure, 300, 200)


class StyleFGChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_metric_values(self.style, 'fg')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'fg', 'count')
        return Chart(figure, 300, 200)


class StylePopularHopsChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_popular_hops(self.style, self.get_use_filter())
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'hop', 'amount_percent', 'Hops by Popularity', '% Amount')
        return Chart(figure)

    def get_use_filter(self):
        if self.filter_param == 'bittering':
            return [RecipeHop.MASH, RecipeHop.FIRST_WORT, RecipeHop.BOIL]
        if self.filter_param == 'aroma':
            return [RecipeHop.AROMA]
        if self.filter_param == 'dry-hop':
            return [RecipeHop.DRY_HOP]
        return []


class StylePopularFermentablesChart(StyleChart):
    def plot(self) -> Chart:
        (categories, types) = self.get_filter()
        df = get_style_popular_fermentables(self.style, categories, types)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'fermentable', 'amount_percent', 'Fermentables by Popularity', '% Amount')
        return Chart(figure)

    def get_filter(self) -> Tuple[list, list]:
        if self.filter_param == 'base':
            return [], [Fermentable.BASE]
        if self.filter_param == 'cara-crystal':
            return [], [Fermentable.CARA_CRYSTAL]
        if self.filter_param == 'toasted':
            return [], [Fermentable.TOASTED]
        if self.filter_param == 'roasted':
            return [], [Fermentable.ROASTED]
        if self.filter_param == 'other-grain':
            return [], [Fermentable.OTHER_MALT, Fermentable.ADJUNCT, Fermentable.UNMALTED_ADJUNCT]
        if self.filter_param == 'sugar':
            return [Fermentable.SUGAR], []
        if self.filter_param == 'fruit':
            return [Fermentable.FRUIT], []

        return [], []


class StyleHopPairingsChart(StyleChart):
    def plot(self) -> Chart:
        df = get_style_hop_pairings(self.style)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'hop', 'amount_percent', None, '% Amount')
        return Chart(figure)


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

    def get_chart(self, style: Style, chart_type: str, filter_param: Optional[str]) -> Chart:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(style, filter_param).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
