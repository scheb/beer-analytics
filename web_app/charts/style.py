from abc import ABC
from typing import Optional, Tuple

from recipe_db.analytics.charts.fermentable import get_style_popular_fermentables
from recipe_db.analytics.charts.hop import get_style_hop_pairings, get_style_popular_hops
from recipe_db.analytics.charts.style import StyleAnalysis
from recipe_db.models import Style, RecipeHop, Fermentable
from web_app.charts.utils import NoDataException, Chart, ChartDefinition
from web_app.meta import OPEN_GRAPH_IMAGE_WIDTH, OPEN_GRAPH_IMAGE_HEIGHT
from web_app.plot import LinesChart, PreAggregatedBoxPlot, \
    PreAggregateHistogramChart, PreAggregatedPairsBoxPlot


class StyleChart(ChartDefinition, ABC):
    CHART_TITLE = None
    IMAGE_ALT = None

    def __init__(self, style: Style, filter_param: Optional[str]) -> None:
        self.style = style
        self.filter_param = filter_param

    def get_chart_title(self) -> str:
        return self.CHART_TITLE % self.style.name

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT % self.style.name


class StyleAbvChart(StyleChart):
    CHART_TITLE = "Alcohol per Volume of <b>%s</b>"
    IMAGE_ALT = "Histogram of Alcohol per Volume (ABV) in the %s beer style"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).metric_histogram('abv')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'abv', 'count')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class StyleIbuChart(StyleChart):
    CHART_TITLE = "Bitterness of <b>%s</b>"
    IMAGE_ALT = "Histogram of bitterness (IBU) in the %s beer style"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).metric_histogram('ibu')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'ibu', 'count')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class StyleColorChart(StyleChart):
    CHART_TITLE = "Color of <b>%s</b>"
    IMAGE_ALT = "Histogram of beer color (SRM) in the %s beer style"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).metric_histogram('srm')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'srm', 'count')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class StyleOGChart(StyleChart):
    CHART_TITLE = "Original Gravity of <b>%s</b>"
    IMAGE_ALT = "Histogram of original gravity (OG) in the %s beer style"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).metric_histogram('og')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'og', 'count')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class StyleFGChart(StyleChart):
    CHART_TITLE = "Final Gravity of <b>%s</b>"
    IMAGE_ALT = "Histogram of final gravity (FG) in the %s beer style"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).metric_histogram('fg')
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregateHistogramChart().plot(df, 'fg', 'count')
        return Chart(figure, 500, 350, title=self.get_chart_title())


class StylePopularityChart(StyleChart):
    CHART_TITLE = "Popularity of <b>%s</b> over time"
    IMAGE_ALT = "Popularity of the %s beer style over time"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).popularity()
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class StyleTrendingHopsChart(StyleChart):
    CHART_TITLE = "Trending hops in <b>%s</b>"
    IMAGE_ALT = "Trending hops in the %s beer style"

    def plot(self) -> Chart:
        df = StyleAnalysis(self.style).trending_hops()
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% Style Recipes')
        return Chart(figure, title=self.get_chart_title())

class StylePopularHopsChart(StyleChart):
    CHART_TITLE = "Popular hops used in <b>%s</b>"
    IMAGE_ALT = "Popular hops used in the %s beer style"

    def plot(self) -> Chart:
        df = get_style_popular_hops(self.style, self.get_use_filter())
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'hop', 'amount_percent', 'Hops by Popularity', '% Amount')
        return Chart(figure, title=self.get_chart_title())

    def get_use_filter(self):
        if self.filter_param == 'bittering':
            return [RecipeHop.MASH, RecipeHop.FIRST_WORT, RecipeHop.BOIL]
        if self.filter_param == 'aroma':
            return [RecipeHop.AROMA]
        if self.filter_param == 'dry-hop':
            return [RecipeHop.DRY_HOP]
        return []


class StylePopularFermentablesChart(StyleChart):
    CHART_TITLE = "Popular fermentables/malts used in <b>%s</b>"
    IMAGE_ALT = "Popular fermentables/malts used in the %s beer style"

    def plot(self) -> Chart:
        (categories, types) = self.get_filter()
        df = get_style_popular_fermentables(self.style, categories, types)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'fermentable', 'amount_percent', 'Fermentables by Popularity', '% Amount')
        return Chart(figure, title=self.get_chart_title())

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
    CHART_TITLE = "Popular hop pairings used in <b>%s</b>"
    IMAGE_ALT = "Popular hop pairings used in the %s beer style"

    def plot(self) -> Chart:
        df = get_style_hop_pairings(self.style)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'hop', 'amount_percent', None, '% Amount')
        return Chart(figure, title=self.get_chart_title())


class StyleOpenGraphChart(StylePopularityChart):
    def plot(self) -> Chart:
        chart = super().plot()
        chart.width = OPEN_GRAPH_IMAGE_WIDTH
        chart.height = OPEN_GRAPH_IMAGE_HEIGHT
        return chart


class StyleChartFactory:
    CHARTS = dict(
        og=StyleOpenGraphChart,
        abv_histogram=StyleAbvChart,
        ibu_histogram=StyleIbuChart,
        color_srm_histogram=StyleColorChart,
        original_gravity_histogram=StyleOGChart,
        final_gravity_histogram=StyleFGChart,
        popularity=StylePopularityChart,
        trending_hops=StyleTrendingHopsChart,
        popular_hops=StylePopularHopsChart,
        popular_fermentables=StylePopularFermentablesChart,
        hop_pairings=StyleHopPairingsChart,
    )

    @classmethod
    def get_chart(cls, style: Style, chart_type: str, filter_param: Optional[str] = "") -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(style, filter_param)

    @classmethod
    def plot_chart(cls, style: Style, chart_type: str, filter_param: Optional[str] = "") -> Chart:
        return cls.get_chart(style, chart_type, filter_param).plot()

    @classmethod
    def is_supported_chart(cls, chart_type: str) -> bool:
        chart_type = cls.normalize_type(chart_type)
        return chart_type in cls.CHARTS

    @classmethod
    def normalize_type(cls, chart_type: str) -> str:
        return chart_type.replace('-', '_')

    @classmethod
    def get_types(cls):
        return list(cls.CHARTS.keys())
