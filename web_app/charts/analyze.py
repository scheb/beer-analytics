from abc import ABC

from recipe_db.analytics.recipe import RecipesTrendAnalysis, RecipesPopularityAnalysis
from recipe_db.analytics.scope import RecipeScope
from web_app.charts.utils import Chart, ChartDefinition, NoDataException
from web_app.plot import LinesChart


class CustomChart(ChartDefinition, ABC):
    CHART_TITLE = 'Custom data analysis'
    IMAGE_ALT = 'Custom data analysis'

    def __init__(self, scope: RecipeScope) -> None:
        self.recipe_scope = scope

    def get_chart_title(self) -> str:
        return self.CHART_TITLE

    def get_image_alt(self) -> str:
        return self.IMAGE_ALT


class TrendingHopsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        df = analysis.trending_hops(trend_window_months=24)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'hop', None, '% of All Recipes')
        return Chart(figure, title=self.get_chart_title())


class PopularHopsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_hop(num_top=8, top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'hop', 'Month/Year', '% of All Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingYeastsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        df = analysis.trending_yeasts(trend_window_months=24)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'yeast', None, '% of All Recipes')
        return Chart(figure, title=self.get_chart_title())


class PopularYeastsChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_yeast(num_top=8, top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'yeast', 'Month/Year', '% of All Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class TrendingStylesChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        df = analysis.trending_styles(trend_window_months=24)
        if len(df) == 0:
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'beer_style', None, '% of All Recipes')
        return Chart(figure, title=self.get_chart_title())


class PopularStylesChart(CustomChart):
    def plot(self) -> Chart:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        df = analysis.popularity_per_style(num_top=8, top_months=24)
        if len(df) <= 1:  # 1, because a single data point is also meaningless
            raise NoDataException()

        figure = LinesChart(force_legend=True).plot(df, 'month', 'recipes_percent', 'beer_style', 'Month/Year', '% of All Recipes')
        return Chart(figure, height=Chart.DEFAULT_HEIGHT * 0.66, title=self.get_chart_title())


class AnalyzeChartFactory:
    CHARTS = dict(
        trending_hops=TrendingHopsChart,
        trending_yeasts=TrendingYeastsChart,
        trending_styles=TrendingStylesChart,
        popular_hops=PopularHopsChart,
        popular_yeasts=PopularYeastsChart,
        popular_styles=PopularStylesChart,
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
