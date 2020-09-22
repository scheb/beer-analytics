from django.http import HttpResponse, HttpRequest
from django.shortcuts import render

from recipe_db.models import Recipe, Style, Hop, Fermentable


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
        'fermentables': fermentables
    }, content_type='text/xml')
