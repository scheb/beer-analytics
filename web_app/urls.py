from django.urls import path, re_path, register_converter

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
    path('imprint', views.imprint, name='imprint'),
    path('privacy-policy', views.privacy_policy, name='privacy_policy'),

    path('trends/', views.home, name='trends'),
    path('hops/', views.home, name='hop_overview'),
    path('fermentables/', views.home, name='fermentable_overview'),

    path('styles/', views.style_overview, name='style_overview'),
    path('styles/<str:category_slug>', views.style_category_detail, name='style_category_detail'),
    path('styles/<str:category_slug>/<str:slug>', views.style_detail, name='style_detail'),
    path('styles/charts/<str:id>/<str:chart_type>.<cformat:format>', views.style_chart, name='style_chart'),
]
