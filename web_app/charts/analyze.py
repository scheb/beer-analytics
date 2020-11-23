from abc import ABC

from recipe_db.analytics.fermentable import FermentableAmountAnalysis
from recipe_db.analytics.hop import HopPairingAnalysis, HopAmountAnalysis
from recipe_db.analytics.recipe import RecipesTrendAnalysis, RecipesPopularityAnalysis, CommonStylesAnalysis
from recipe_db.analytics.scope import RecipeScope
from web_app.charts.utils import Chart, ChartDefinition, NoDataException
from web_app.plot import LinesChart, BarChart, PreAggregatedPairsBoxPlot, PreAggregatedBoxPlot


class CustomChart(ChartDefinition, ABC):
    CHART_TITLE = 'Custom data analysis'
    IMAGE_ALT = 'Custom data analysis'

    def __init__(self, scope: RecipeScope) -> None:
        self.recipe_scope = scope

    def get_chart_title(self) -> str:
        return self.CHART_TITLE

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT


class PopularStylesChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_style(num_top=8, top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'beer_style', 'Month/Year', '% of All Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingStylesChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        df = analysis.trending_styles(trend_window_months=24)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'beer_style', None, '% of All Recipes')
        return Chart(figure, title=self.get_chart_title())


class StylesAbsoluteChart(CustomChart):
    def plot(self) -> Chart:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        df = analysis.common_styles_absolute(num_top=20)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'beer_style', 'recipes', None, 'Total Number of Recipes')
        return Chart(figure, title=self.get_chart_title())


class StylesRelativeChart(CustomChart):
    def plot(self) -> Chart:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        df = analysis.common_styles_relative(num_top=20)
        if len(df) == 0:
            raise NoDataException()

        figure = BarChart().plot(df, 'beer_style', 'recipes_percent', None, '% of the Style\'s Recipes')
        return Chart(figure, title=self.get_chart_title())


class PopularHopsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_hop(num_top=8, top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% of All Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingHopsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        df = analysis.trending_hops(trend_window_months=24)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'hop', None, '% of All Recipes')
        return Chart(figure, title=self.get_chart_title())


class PopularHopsAmountChart(CustomChart):
    def plot(self) -> Chart:
        analysis = HopAmountAnalysis(self.recipe_scope)
        df = analysis.per_hop(num_top=8)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'hop', 'amount_percent', None, '% of Weight in Recipe')
        return Chart(figure, title=self.get_chart_title())


class HopPairingsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = HopPairingAnalysis(self.recipe_scope)
        df = analysis.pairings()
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedPairsBoxPlot().plot(df, 'pairing', 'hop', 'amount_percent', None, '% of Weight in Recipe')
        return Chart(figure, title=self.get_chart_title())


class PopularFermentablesChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_fermentable(num_top=8)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'fermentable', None, '% of Style Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class PopularFermentablesAmountChart(CustomChart):
    def plot(self) -> Chart:
        analysis = FermentableAmountAnalysis(self.recipe_scope)
        df = analysis.per_fermentable(num_top=8)
        if len(df) == 0:
            raise NoDataException()

        figure = PreAggregatedBoxPlot().plot(df, 'fermentable', 'amount_percent', None, '% of Weight in Recipe')
        return Chart(figure, title=self.get_chart_title())


class PopularYeastsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_yeast(num_top=8, top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'yeast', 'Month/Year', '% of All Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingYeastsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        df = analysis.trending_yeasts(trend_window_months=24)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'yeast', None, '% of All Recipes')
        return Chart(figure, title=self.get_chart_title())


class AnalyzeChartFactory:
    CHARTS = dict(
        popular_styles=PopularStylesChart,
        trending_styles=TrendingStylesChart,
        typical_styles_relative=StylesRelativeChart,
        typical_styles_absolute=StylesAbsoluteChart,

        popular_fermentables=PopularFermentablesChart,
        popular_fermentables_amount=PopularFermentablesAmountChart,

        popular_hops=PopularHopsChart,
        trending_hops=TrendingHopsChart,
        popular_hops_amount=PopularHopsAmountChart,
        hop_pairings=HopPairingsChart,

        popular_yeasts=PopularYeastsChart,
        trending_yeasts=TrendingYeastsChart,
    )

    @classmethod
    def get_chart(cls, chart_type: str, scope: RecipeScope) -> ChartDefinition:
        chart_type = cls.normalize_type(chart_type)
        chart = cls.CHARTS[chart_type]
        return chart(scope)

    @classmethod
    def plot_chart(cls, chart_type: str, scope: RecipeScope) -> Chart:
        return cls.get_chart(chart_type, scope).plot()

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
