from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render
from django.urls import reverse

from recipe_db.models import Recipe, Style, Hop, Fermentable, Yeast
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.home import HomeChartFactory
from web_app.charts.hop import HopChartFactory
from web_app.charts.style import StyleChartFactory
from web_app.charts.utils import NoDataException
from web_app.charts.yeast import YeastChartFactory
from web_app.meta import PageMeta, HomeMeta
from web_app.views.utils import render_chart


def home(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    meta = HomeMeta().get_meta()
    return render(request, 'index.html', {'recipes': recipes, 'meta': meta})


def home_chart(request: HttpRequest, chart_type: str, format: str) -> HttpResponse:
    if HomeChartFactory.is_supported_chart(chart_type):
        try:
            chart = HomeChartFactory.plot_chart(chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)


def legal(request: HttpRequest) -> HttpResponse:
    meta = PageMeta.create('Legal', 'Legal information about Beer Analytics', url=reverse('legal'))
    meta.extra_props = {'robots': 'noindex'}
    return render(request, 'legal.html', {'meta': meta})


def about(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    meta = PageMeta.create('About', url=reverse('about'))
    return render(request, 'about.html', {'recipes': recipes, 'meta': meta})


def sitemap(request: HttpRequest) -> HttpResponse:
    styles = Style.objects.filter(recipes_count__gt=0)
    hops = Hop.objects.filter(recipes_count__gt=0)
    fermentables = Fermentable.objects.filter(recipes_count__gt=0)
    yeasts = Yeast.objects.filter(recipes_count__gt=0)

    return render(request, 'sitemap.xml', {
        'styles': styles,
        'hops': hops,
        'fermentables': fermentables,
        'yeasts': yeasts,
        'style_chart_types': StyleChartFactory.get_types(),
        'hop_chart_types': HopChartFactory.get_types(),
        'fermentable_chart_types': FermentableChartFactory.get_types(),
        'yeast_chart_types': YeastChartFactory.get_types(),
    }, content_type='text/xml')


def analyze(request: HttpRequest) -> HttpResponse:
    meta = PageMeta.create('Analyze', '', url=reverse('legal'))
    meta.extra_props = {'robots': 'noindex'}
    return render(request, 'analyze.html', {'meta': meta})
