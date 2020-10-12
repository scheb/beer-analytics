from abc import ABC

from recipe_db.analytics.charts.yeast import YeastAnalysis
from recipe_db.models import Yeast
from web_app.charts.utils import NoDataException, Chart, ChartDefinition
from web_app.meta import OPEN_GRAPH_IMAGE_WIDTH, OPEN_GRAPH_IMAGE_HEIGHT
from web_app.plot import LinesChart, BarChart


class YeastChart(ChartDefinition, ABC):
    CHART_TITLE = None
    IMAGE_ALT = None

    def __init__(self, yeast: Yeast) -> None:
        self.yeast = yeast

    def get_chart_title(self) -> str:
        return self.CHART_TITLE % self.yeast.name

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT % self.yeast.name


class YeastPopularityChart(YeastChart):
    CHART_TITLE = "Popularity of <b>%s</b> yeast over time"
    IMAGE_ALT = "Popularity of the %s yeast over time"

    def plot(self) -> Chart:
        df = YeastAnalysis(self.yeast).popularity()
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart().plot(df, 'month', 'recipes_percent', 'yeast', 'Month/Year', '% Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class YeastCommonStylesAbsoluteChart(YeastChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> yeast (by number of recipes)"
    IMAGE_ALT = "Typical beer styles using %s yeast (by number of recipes)"

    def plot(self) -> Chart:
        df = YeastAnalysis(self.yeast).common_styles_absolute()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes', 'Style', 'Number Recipes')
        return Chart(figure, title=self.get_chart_title())


class YeastCommonStylesRelativeChart(YeastChart):
    CHART_TITLE = "Typical beer styles using <b>%s</b> yeast (by percent of recipes)"
    IMAGE_ALT = "Typical beer styles using %s yeast (by percent of recipes)"

    def plot(self) -> Chart:
        df = YeastAnalysis(self.yeast).common_styles_relative()
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'style_name', 'recipes_percent', 'Style', 'Used in % Recipes')
        return Chart(figure, title=self.get_chart_title())


class YeastOpenGraphChart(YeastPopularityChart):
    def plot(self) -> Chart:
        chart = super().plot()
        chart.width = OPEN_GRAPH_IMAGE_WIDTH
        chart.height = OPEN_GRAPH_IMAGE_HEIGHT
        return chart


class YeastChartFactory:
    CHARTS = dict(
        og=YeastOpenGraphChart,
        popularity=YeastPopularityChart,
        typical_styles_absolute=YeastCommonStylesAbsoluteChart,
        typical_styles_relative=YeastCommonStylesRelativeChart,
    )

    @classmethod
    def get_chart(cls, yeast: Yeast, chart_type: str) -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(yeast)

    @classmethod
    def plot_chart(cls, yeast: Yeast, chart_type: str) -> Chart:
        return cls.get_chart(yeast, chart_type).plot()

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
