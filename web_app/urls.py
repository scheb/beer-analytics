from django.urls import path, register_converter

from . import views

class ChartFormat:
    regex = 'png|svg|json'

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)

register_converter(ChartFormat, 'cformat')

urlpatterns = [
    path('', views.home, name='home'),
    path('imprint', views.legal, name='legal'),

    path('styles/', views.style_overview, name='style_overview'),
    path('styles/<str:category_slug>/', views.style_category_detail, name='style_category_detail'),
    path('styles/<str:category_slug>/<str:slug>', views.style_detail, name='style_detail'),
    path('styles/charts/<str:id>/<str:chart_type>.<cformat:format>', views.style_chart, name='style_chart'),

    path('hops/', views.hop_overview, name='hop_overview'),
    path('hops/<str:category>/', views.hop_category_detail, name='hop_category_detail'),
    path('hops/<str:category>/<str:slug>', views.hop_detail, name='hop_detail'),
    path('hops/charts/<str:id>/<str:chart_type>.<cformat:format>', views.hop_chart, name='hop_chart'),

    path('fermentables/', views.home, name='fermentable_overview'),
]
