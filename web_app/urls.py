from django.urls import path, register_converter

from . import views
from .views import fermentable, hop, misc, style, yeast
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
    path('imprint', misc.legal, name='legal'),

    path('styles/', style.overview, name='style_overview'),
    path('styles/<str:category_slug>/', style.category_detail, name='style_category_detail'),
    path('styles/<str:category_slug>/<str:slug>', style.detail, name='style_detail'),
    path('styles/charts/<str:id>/<str:chart_type>.<cformat:format>', style.chart, name='style_chart'),

    path('hops/', views.hop.overview, name='hop_overview'),
    path('hops/<str:category>/', hop.category_detail, name='hop_category_detail'),
    path('hops/<str:category>/<str:slug>', hop.detail, name='hop_detail'),
    path('hops/charts/<str:id>/<str:chart_type>.<cformat:format>', hop.chart, name='hop_chart'),

    path('fermentables/', fermentable.overview, name='fermentable_overview'),
    path('fermentables/<str:category>/', fermentable.category_detail, name='fermentable_category_detail'),
    path('fermentables/<str:category>/<str:slug>', fermentable.detail, name='fermentable_detail'),
    path('fermentables/charts/<str:id>/<str:chart_type>.<cformat:format>', fermentable.chart, name='fermentable_chart'),

    path('yeasts/', views.yeast.overview, name='yeast_overview'),
]
