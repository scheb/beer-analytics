from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from recipe_db.models import Recipe, Style, Hop, Fermentable
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.hop import HopChartFactory
from web_app.charts.style import StyleChartFactory


def home(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    return render(request, 'index.html', {'recipes': recipes})


def legal(request: HttpRequest) -> HttpResponse:
    return render(request, 'legal.html')


def about(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    return render(request, 'about.html', {'recipes': recipes})


def sitemap(request: HttpRequest) -> HttpResponse:
    styles = Style.objects.filter(recipes_count__gt=0)
    hops = Hop.objects.filter(recipes_count__gt=0)
    fermentables = Fermentable.objects.filter(recipes_count__gt=0)

    return render(request, 'sitemap.xml', {
        'styles': styles,
        'hops': hops,
        'fermentables': fermentables,
        'style_chart_types': StyleChartFactory.get_types(),
        'hop_chart_types': HopChartFactory.get_types(),
        'fermentable_chart_types': FermentableChartFactory.get_types(),
    }, content_type='text/xml')
