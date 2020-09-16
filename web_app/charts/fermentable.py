import abc

from recipe_db.analytics import get_fermentable_popularity, get_fermentable_common_styles
from recipe_db.models import Fermentable
from web_app.plot import Plot, LinesChart, BarChart


class FermentableChart:
    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class FermentablePopularityChart(FermentableChart):
    def plot(self) -> Plot:
        df = get_fermentable_popularity(self.fermentable)
        return LinesChart().plot(df, 'month', 'recipes_percent', 'fermentable', 'Month/Year', '% Recipes')


class FermentableCommonStylesChart(FermentableChart):
    def plot(self) -> Plot:
        df = get_fermentable_common_styles(self.fermentable)
        return BarChart().plot(df, 'style_name', 'recipes_percent', 'Style', 'Used in % Recipes')


class FermentableChartFactory:
    CHARTS = dict(
        popularity=FermentablePopularityChart,
        styles=FermentableCommonStylesChart,
    )

    def get_chart(self, fermentable: Fermentable, chart_type: str) -> Plot:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(fermentable).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
