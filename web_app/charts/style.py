import abc

from recipe_db.analytics import get_style_hop_pairings, get_style_popular_fermentables, get_style_popular_hops, \
    get_style_metric_values, get_style_popularity
from recipe_db.models import Style
from web_app.plot import Plot, LinesChart, PreAggregatedBoxPlot, \
    PreAggregateHistogramChart, PreAggregatedPairsBoxPlot


class StyleChart:
    def __init__(self, style: Style) -> None:
        self.style = style

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class StylePopularityChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_popularity(self.style)
        return LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes')


class StyleAbvChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'abv')
        return PreAggregateHistogramChart().plot(df, 'abv', 'count')


class StyleIbuChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'ibu')
        return PreAggregateHistogramChart().plot(df, 'ibu', 'count')


class StyleColorChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'srm')
        return PreAggregateHistogramChart().plot(df, 'srm', 'count')


class StyleOGChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'og')
        return PreAggregateHistogramChart().plot(df, 'og', 'count')


class StyleFGChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_metric_values(self.style, 'fg')
        return PreAggregateHistogramChart().plot(df, 'fg', 'count')


class StylePopularHopsChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_popular_hops(self.style)
        return PreAggregatedBoxPlot().plot(df, 'hop', 'amount_percent', 'Hops by Popularity', '% Amount')


class StylePopularFermentablesChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_popular_fermentables(self.style)
        return PreAggregatedBoxPlot().plot(df, 'fermentable', 'amount_percent', 'Fermentables by Popularity', '% Amount')


class StyleHopPairingsChart(StyleChart):
    def plot(self) -> Plot:
        df = get_style_hop_pairings(self.style)
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

    def get_chart(self, style: Style, chart_type: str) -> Plot:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(style).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
