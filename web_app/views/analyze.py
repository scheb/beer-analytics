import json
from typing import List, Tuple, Optional

from django.http import HttpResponse, HttpRequest, Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.recipe import RecipesCountAnalysis, RecipesListAnalysis
from recipe_db.analytics.scope import RecipeScope
from recipe_db.etl.format.parser import int_or_none
from recipe_db.models import Style, Hop, Fermentable, Yeast
from web_app import DEFAULT_PAGE_CACHE_TIME
from web_app.charts.analyze import AnalyzeChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import PageMeta
from web_app.views.utils import render_chart, FORMAT_JSON, render_recipes_list, no_data_response


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="default")
def result(request: HttpRequest) -> HttpResponse:
    meta = PageMeta.create("Custom Analysis", "", url=reverse("legal"))
    meta.extra_props = {"robots": "noindex"}
    return render(request, "analyze.html", {"meta": meta})


@cache_page(0)
def count(request: HttpRequest) -> HttpResponse:
    recipes_scope = get_scope(request)
    count = RecipesCountAnalysis(recipes_scope).total()
    return HttpResponse(json.dumps({"count": count}), content_type="application/json")


@cache_page(0)
def chart(request: HttpRequest, chart_type: str) -> HttpResponse:
    recipes_scope = get_scope(request)
    if AnalyzeChartFactory.is_supported_chart(chart_type):
        try:
            chart = AnalyzeChartFactory.plot_chart(chart_type, recipes_scope)
        except NoDataException:
            return no_data_response()
    else:
        raise Http404("Unknown chart type %s." % chart_type)

    return render_chart(chart, FORMAT_JSON)


@cache_page(0)
def recipes(request: HttpRequest) -> HttpResponse:
    recipes_scope = get_scope(request)
    analysis = RecipesListAnalysis(recipes_scope)
    recipes_list = analysis.random(24)
    return render_recipes_list(request, recipes_list, "Analyze")


def get_scope(request: HttpRequest) -> RecipeScope:
    recipe_scope = RecipeScope()

    if "term" in request.GET:
        recipe_scope.search_term = str(request.GET['term']).strip() if len(str(request.GET['term']).strip()) > 0 else None

    if "styles" in request.GET:
        recipe_scope.style_criteria = get_style_criteria(str(request.GET["styles"]))
    if "hops" in request.GET:
        recipe_scope.hop_criteria = get_hop_criteria(str(request.GET["hops"]))
    if "fermentables" in request.GET:
        recipe_scope.fermentable_criteria = get_fermentable_criteria(str(request.GET["fermentables"]))
    if "yeasts" in request.GET:
        recipe_scope.yeast_criteria = get_yeast_criteria(str(request.GET["yeasts"]))

    if "ibu" in request.GET:
        (recipe_scope.ibu_min, recipe_scope.ibu_max) = get_min_max(str(request.GET["ibu"]), 0, 301)
    if "abv" in request.GET:
        (recipe_scope.abv_min, recipe_scope.abv_max) = get_min_max(str(request.GET["abv"]), 0, 21)
    if "srm" in request.GET:
        (recipe_scope.srm_min, recipe_scope.srm_max) = get_min_max(str(request.GET["srm"]), 0, 101)
    if "og" in request.GET:
        (recipe_scope.og_min, recipe_scope.og_max) = get_min_max(str(request.GET["og"]), 1000, 1151, factor=0.001)

    return recipe_scope


def get_style_criteria(value: str) -> Optional[RecipeScope.StyleCriteria]:
    style_ids = list(map(str.strip, value.split(",")))
    styles = Style.objects.filter(id__in=style_ids)

    if styles.count() > 0:
        style_criteria = RecipeScope.StyleCriteria()
        style_criteria.styles = styles
        return style_criteria

    return None


def get_hop_criteria(value: str) -> Optional[RecipeScope.HopCriteria]:
    hops_ids = list(map(str.strip, value.split(",")))
    hops = Hop.objects.filter(id__in=hops_ids)

    if hops.count() > 0:
        hop_criteria = RecipeScope.HopCriteria()
        hop_criteria.hops = hops
        return hop_criteria

    return None


def get_fermentable_criteria(value: str) -> Optional[RecipeScope.FermentableCriteria]:
    fermentable_ids = list(map(str.strip, value.split(",")))
    fermentables = Fermentable.objects.filter(id__in=fermentable_ids)

    if fermentables.count() > 0:
        fermentable_criteria = RecipeScope.FermentableCriteria()
        fermentable_criteria.fermentables = fermentables
        return fermentable_criteria

    return None


def get_yeast_criteria(value: str) -> Optional[RecipeScope.YeastCriteria]:
    yeasts_ids = list(map(str.strip, value.split(",")))
    yeasts = Yeast.objects.filter(id__in=yeasts_ids)

    if yeasts.count() > 0:
        yeast_criteria = RecipeScope.YeastCriteria()
        yeast_criteria.yeasts = yeasts
        return yeast_criteria

    return None


def get_min_max(value: str, min_limit: int, max_limit: int, factor: float = 1) -> Tuple:
    values = list(map(str.strip, value.split(",")))
    if len(values) < 2:
        return None, None  # Not enough values

    min_value = int_or_none(values[0])
    if min_value is not None and min_value <= min_limit:  # Limit values are a "no filter"
        min_value = None

    max_value = int_or_none(values[1])
    if max_value is not None and max_value >= max_limit:  # Limit values are a "no filter"
        max_value = None

    return min_value * factor if min_value is not None else None, max_value * factor if max_value is not None else None


@cache_page(DEFAULT_PAGE_CACHE_TIME, cache="data")
def get_entities(request: HttpRequest) -> HttpResponse:
    styles = Style.objects.exclude(parent_style=None).filter(recipes_count__gt=0).order_by('id')
    hops = Hop.objects.all().filter(recipes_count__gt=0).order_by('name')
    fermentables = Fermentable.objects.all().filter(recipes_count__gt=0).order_by('name')
    yeasts = Yeast.objects.all().filter(recipes_count__gt=0).order_by('name')

    return JsonResponse({
        "styles": list(map(lambda s: {"id": s.id, "name": s.name, "parent": s.parent_style_name}, styles)),
        "hops": list(map(lambda h: {"id": h.id, "name": h.name}, hops)),
        "fermentables": list(map(lambda f: {"id": f.id, "name": f.name}, fermentables)),
        "yeasts": list(sorted(map(lambda y: {"id": y.id, "name": y.full_name_incl_product_id}, yeasts), key=lambda x: x['name'])),
    })
