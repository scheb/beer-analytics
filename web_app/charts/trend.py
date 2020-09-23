from abc import ABC

from recipe_db.analytics import get_hops_popularity, get_styles_popularity
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
    IDS = ["02A", "12C", "23A"]

    def get_chart_title(self) -> str:
        return "Trending beer styles"

    def get_image_alt(self) -> str:
        return "Trending beer styles"


class WinterStylesChart(StylesPopularityChart):
    IDS = ["30A", "30B", "30C", "16A", "16B", "20A", "20B", "20C"]

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


class FutureHopsPopularityChart(HopsPopularityChart):
    IDS = ["sabro", "cashmere", "idaho-7"]

    def get_chart_title(self) -> str:
        return "Trending Hops"

    def get_image_alt(self) -> str:
        return "Trending Hops"


class PresentHopsPopularityChart(HopsPopularityChart):
    IDS = ["galaxy", "mosaic", "lemondrop"]

    def get_chart_title(self) -> str:
        return "Currently popular hops"

    def get_image_alt(self) -> str:
        return "Currently popular hops"


class PastHopsPopularityChart(HopsPopularityChart):
    IDS = ["el-dorado", "azacca"]

    def get_chart_title(self) -> str:
        return "Hops with decreasing popularity"

    def get_image_alt(self) -> str:
        return "Hops with decreasing popularity"


class TrendChartFactory:
    CHARTS = dict(
        trending_styles=TrendingStylesChart,
        winter_styles=WinterStylesChart,
        future_hops=FutureHopsPopularityChart,
        present_hops=PresentHopsPopularityChart,
        past_hops=PastHopsPopularityChart,
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
