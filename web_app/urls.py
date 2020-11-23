from django.urls import path, register_converter

from . import views
from .views import fermentable, hop, misc, style, yeast, trend, analyze
from .views.utils import FORMATS


class ChartFormat:
    regex = '|'.join(FORMATS)

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)


register_converter(ChartFormat, 'cformat')


urlpatterns = [
    path('', views.misc.home, name='home'),
    path('legal/', misc.legal, name='legal'),
    path('about/', misc.about, name='about'),
    path('sitemap.xml', misc.sitemap, name='sitemap'),

    path('analyze/', analyze.result, name='analyze'),
    path('analyze/count.json', analyze.count, name='analyze_count'),
    path('analyze/<str:chart_type>.json', analyze.chart, name='analyze_chart'),

    path('styles/', style.overview, name='style_overview'),
    path('styles/<str:category_slug>/', style.category, name='style_category'),
    path('styles/<str:category_slug>/charts/<str:chart_type>.<cformat:format>', style.category_chart, name='style_category_chart'),
    path('styles/<str:category_slug>/recipes/random.json', style.category_recipes, name='style_category_recipes'),
    path('styles/<str:category_slug>/<str:slug>/', style.detail, name='style_detail'),
    path('styles/<str:category_slug>/<str:slug>/charts/<str:chart_type>.<cformat:format>', style.chart, name='style_chart'),
    path('styles/<str:category_slug>/<str:slug>/recipes/random.json', style.recipes, name='style_recipes'),

    path('hops/', views.hop.overview, name='hop_overview'),
    path('hops/<str:category_id>/', hop.category_or_tag, name='hop_category'),
    path('hops/<str:category_id>/<str:slug>/', hop.detail, name='hop_detail'),
    path('hops/<str:category_id>/<str:slug>/charts/<str:chart_type>.<cformat:format>', hop.chart, name='hop_chart'),
    path('hops/<str:category_id>/<str:slug>/recipes/random.json', hop.recipes, name='hop_recipes'),

    path('fermentables/', fermentable.overview, name='fermentable_overview'),
    path('fermentables/<str:category_id>/', fermentable.category, name='fermentable_category'),
    path('fermentables/<str:category_id>/<str:slug>/', fermentable.detail, name='fermentable_detail'),
    path('fermentables/<str:category_id>/<str:slug>/charts/<str:chart_type>.<cformat:format>', fermentable.chart, name='fermentable_chart'),
    path('fermentables/<str:category_id>/<str:slug>/recipes/random.json', fermentable.recipes, name='fermentable_recipes'),

    path('yeasts/', yeast.overview, name='yeast_overview'),
    path('yeasts/<str:type_id>/', yeast.type_overview, name='yeast_type'),
    path('yeasts/<str:type_id>/<str:slug>/', yeast.detail, name='yeast_detail'),
    path('yeasts/<str:type_id>/<str:slug>/charts/<str:chart_type>.<cformat:format>', yeast.chart, name='yeast_chart'),
    path('yeasts/<str:type_id>/<str:slug>/recipes/random.json', yeast.recipes, name='yeast_recipes'),

    path('trends/', trend.start, name='trend_root'),
    path('trends/<str:period>/', trend.overview, name='trend_overview'),
    path('trends/<str:period>/<str:chart_type>.<cformat:format>', trend.chart, name='trend_chart'),
]
