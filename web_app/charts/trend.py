from abc import ABC

from recipe_db.analytics import get_hops_popularity, get_styles_popularity, get_most_popular_hops
from recipe_db.models import Hop, Style
from web_app.charts.utils import NoDataException, Chart, ChartDefinition
from web_app.plot import LinesChart


class StylesPopularityChart(ChartDefinition, ABC):
    IDS = []

    def __init__(self) -> None:
        self.styles = Style.objects.filter(pk__in=self.IDS)

    def plot(self) -> Chart:
        df = get_styles_popularity(self.styles)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingStylesChart(StylesPopularityChart):
    IDS = ["02A", "12C"]

    def get_chart_title(self) -> str:
        return "Trending beer styles"

    def get_image_alt(self) -> str:
        return "Trending beer styles"


class WinterStylesChart(StylesPopularityChart):
    IDS = ["30A", "30B", "30C", "16B", "20A", "20C"]

    def get_chart_title(self) -> str:
        return "Trending winter beer styles"

    def get_image_alt(self) -> str:
        return "Trending winter beer styles"


class HopsPopularityChart(ChartDefinition, ABC):
    IDS = []

    def __init__(self) -> None:
        self.hops = Hop.objects.filter(pk__in=self.IDS)

    def plot(self) -> Chart:
        df = get_hops_popularity(self.hops)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class IncreasingHopsPopularityChart(HopsPopularityChart):
    IDS = ["sabro", "cashmere", "idaho-7"]

    def get_chart_title(self) -> str:
        return "Trending hops"

    def get_image_alt(self) -> str:
        return "Trending hops"


class PlateauingHopsPopularityChart(HopsPopularityChart):
    IDS = ["lemondrop", "el-dorado", "azacca"]

    def get_chart_title(self) -> str:
        return "Previously trending hops"

    def get_image_alt(self) -> str:
        return "Previously trending hops"


class FavouriteHopsPopularityChart(ChartDefinition):
    def get_chart_title(self) -> str:
        return "Brewer's favourite hops"

    def get_image_alt(self) -> str:
        return "Brewer's favourite hops"

    def plot(self) -> Chart:
        df = get_most_popular_hops()
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendChartFactory:
    CHARTS = dict(
        trending_styles=TrendingStylesChart,
        winter_styles=WinterStylesChart,
        increasing_popularity_hops=IncreasingHopsPopularityChart,
        plateauing_popularity_hops=PlateauingHopsPopularityChart,
        favourite_hops=FavouriteHopsPopularityChart,
    )

    @classmethod
    def get_chart(cls, chart_type: str) -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart()

    @classmethod
    def plot_chart(cls, chart_type: str) -> Chart:
        return cls.get_chart(chart_type).plot()

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
