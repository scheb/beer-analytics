import json
from typing import List, Tuple

from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.recipe import RecipesCountAnalysis
from recipe_db.analytics.scope import RecipeScope
from recipe_db.etl.format.parser import int_or_none
from recipe_db.models import Style
from web_app.charts.analyze import AnalyzeChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import PageMeta
from web_app.views.utils import render_chart, FORMAT_JSON


def result(request: HttpRequest) -> HttpResponse:
    meta = PageMeta.create('Custom Analysis', '', url=reverse('legal'))
    meta.extra_props = {'robots': 'noindex'}
    return render(request, 'analyze.html', {'meta': meta})


@cache_page(0)
def count(request: HttpRequest) -> HttpResponse:
    recipes_scope = get_scope(request)
    count = RecipesCountAnalysis(recipes_scope).total()
    return HttpResponse(json.dumps({'count': count}), content_type='application/json')


@cache_page(0)
def chart(request: HttpRequest, chart_type: str) -> HttpResponse:
    recipes_scope = get_scope(request)
    if AnalyzeChartFactory.is_supported_chart(chart_type):
        try:
            chart = AnalyzeChartFactory.plot_chart(chart_type, recipes_scope)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, FORMAT_JSON)


def get_scope(request: HttpRequest) -> RecipeScope:
    scope = RecipeScope()

    # Update values in data.ts when limits are changed
    if 'styles' in request.GET:
        scope.styles = get_styles(str(request.GET['styles']))
    if 'ibu' in request.GET:
        (scope.ibu_min, scope.ibu_max) = get_min_max(str(request.GET['ibu']), 0, 301)
    if 'abv' in request.GET:
        (scope.abv_min, scope.abv_max) = get_min_max(str(request.GET['abv']), 0, 21)
    if 'srm' in request.GET:
        (scope.srm_min, scope.srm_max) = get_min_max(str(request.GET['srm']), 0, 101)
    if 'og' in request.GET:
        (scope.og_min, scope.og_max) = get_min_max(str(request.GET['og']), 1000, 1151, factor=0.001)

    return scope


def get_styles(value: str) -> List[Style]:
    style_ids = list(map(str.strip, value.split(',')))
    return Style.objects.filter(id__in=style_ids)


def get_min_max(value: str, min_limit: int, max_limit: int, factor: float = 1) -> Tuple:
    values = list(map(str.strip, value.split(',')))
    if len(values) < 2:
        return None, None  # Not enough values

    min_value = int_or_none(values[0])
    if min_value is not None and min_value <= min_limit:  # Limit values are a "no filter"
        min_value = None

    max_value = int_or_none(values[1])
    if max_value is not None and max_value >= max_limit:  # Limit values are a "no filter"
        max_value = None

    return min_value*factor if min_value is not None else None, max_value*factor if max_value is not None else None
