import abc

from recipe_db.analytics import get_hop_popularity, get_hop_common_styles
from recipe_db.models import Hop
from web_app.plot import Plot, LinesChart, BarChart


class HopChart:
    def __init__(self, hop: Hop) -> None:
        self.hop = hop

    @abc.abstractmethod
    def plot(self) -> None:
        raise NotImplementedError


class HopPopularityChart(HopChart):
    def plot(self) -> Plot:
        df = get_hop_popularity(self.hop)
        return LinesChart().plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% Recipes')


class HopCommonStylesChart(HopChart):
    def plot(self) -> Plot:
        df = get_hop_common_styles(self.hop)
        return BarChart().plot(df, 'style_name', 'recipes_percent', 'Style', 'Used in % Recipes')


class HopPairingsChart(HopChart):
    def plot(self) -> Plot:
        pass


class HopChartFactory:
    CHARTS = dict(
        popularity=HopPopularityChart,
        styles=HopCommonStylesChart,
        pairings=HopPairingsChart,
    )

    def get_chart(self, hop: Hop, chart_type: str) -> Plot:
        chart_type = self.normalize_type(chart_type)
        chart = self.CHARTS[chart_type]
        return chart(hop).plot()

    def is_supported_chart(self, chart_type: str) -> bool:
        chart_type = self.normalize_type(chart_type)
        return chart_type in self.CHARTS

    def normalize_type(self, chart_type: str) -> str:
        return chart_type.replace('-', '_')
