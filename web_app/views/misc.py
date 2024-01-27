from django.http import HttpResponse, HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.models import Recipe, Style, Hop, Fermentable, Yeast, Tag
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.fermentable import FermentableChartFactory
from web_app.charts.hop import HopChartFactory
from web_app.charts.style import StyleChartFactory
from web_app.charts.yeast import YeastChartFactory
from web_app.meta import PageMeta, HomeMeta

FEATURED_HOPS = ['talus', 'nectaron', 'hbc-586', 'vic-secret']

@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def home(request: HttpRequest) -> HttpResponse:
    discover_hops = Hop.objects.filter(id__in=FEATURED_HOPS).order_by('-search_popularity')

    recipes = Recipe.objects.count()
    meta = HomeMeta().get_meta()
    context = {
        "recipes": recipes,
        "meta": meta,
        "discover_hops": discover_hops,
    }

    return render(request, "index.html", context)


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def legal(request: HttpRequest) -> HttpResponse:
    meta = PageMeta.create("Legal", "Legal information about Beer Analytics", url=reverse("legal"))
    meta.extra_props = {"robots": "noindex"}
    return render(request, "legal.html", {"meta": meta})


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def about(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    meta = PageMeta.create("About", url=reverse("about"))
    return render(request, "about.html", {"recipes": recipes, "meta": meta})


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def updates(request: HttpRequest) -> HttpResponse:
    meta = PageMeta.create("Recent Updates", "Recent updates on Beer Analytics", url=reverse("updates"))
    meta.extra_props = {"robots": "noindex"}
    return render(request, "updates.html", {"meta": meta})


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def sitemap(request: HttpRequest) -> HttpResponse:
    styles = Style.objects.filter(recipes_count__gt=0)
    hops = Hop.objects.all()
    fermentables = Fermentable.objects.filter(recipes_count__gt=0)
    yeasts = Yeast.objects.filter(recipes_count__gt=0)
    tags = Tag.objects.all()

    return render(
        request,
        "sitemap.xml",
        {
            "styles": styles,
            "hops": hops,
            "fermentables": fermentables,
            "yeasts": yeasts,
            "tags": tags,
            "style_chart_types": StyleChartFactory.get_types(),
            "hop_chart_types": HopChartFactory.get_types(),
            "fermentable_chart_types": FermentableChartFactory.get_types(),
            "yeast_chart_types": YeastChartFactory.get_types(),
        },
        content_type="text/xml",
    )
