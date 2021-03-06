from typing import Tuple

from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.spotlight.yeast import YeastAnalysis
from recipe_db.models import Yeast
from web_app.charts.utils import NoDataException
from web_app.charts.yeast import YeastChartFactory
from web_app.meta import YeastMeta, YeastOverviewMeta
from web_app.views.utils import render_chart, FORMAT_PNG, render_recipes_list


def overview(request: HttpRequest) -> HttpResponse:
    yeasts = Yeast.objects.filter(recipes_count__gt=0).order_by('name')
    yeast_types = group_by_type(yeasts)
    for yeast_type in yeast_types:
        if len(yeast_type['yeasts']) > 5:
            yeast_type['most_popular'] = Yeast.objects.filter(type=yeast_type['id']).order_by('-recipes_count')[:5]
        (yeast_type['yeasts'], yeast_type['labs']) = group_by_lab(yeast_type['yeasts'])

    meta = YeastOverviewMeta().get_meta()
    context = {'types': yeast_types, 'meta': meta}

    return render(request, 'yeast/overview.html', context)


def type_overview(request: HttpRequest, type_id: str) -> HttpResponse:
    types = Yeast.get_types()
    if type_id not in types:
        raise Http404('Unknown yeast type %s.' % type_id)

    type_name = types[type_id]

    yeasts_query = Yeast.objects.filter(type=type_id, recipes_count__gt=0)
    (yeasts, labs) = group_by_lab(yeasts_query.order_by('name'))

    most_popular = []
    if yeasts_query.count() > 5:
        most_popular = yeasts_query.order_by('-recipes_count')[:5]

    meta = YeastOverviewMeta((type_id, type_name)).get_meta()
    context = {
        'type_name': type_name,
        'yeasts': yeasts,
        'labs': labs,
        'most_popular': most_popular,
        'meta': meta,
    }

    return render(request, 'yeast/type.html', context)


def detail(request: HttpRequest, slug: str, type_id: str) -> HttpResponse:
    yeast = get_object_or_404(Yeast, pk=slug)

    if yeast.recipes_count <= 0:
        raise Http404("Yeast doesn't have any data.")

    if type_id != yeast.type or slug != yeast.id:
        return redirect('yeast_detail', type=yeast.type, slug=yeast.id)

    meta_provider = YeastMeta(yeast)
    meta = meta_provider.get_meta()
    if yeast.recipes_count > 100:
        meta.image = reverse('yeast_chart', kwargs=dict(
            type_id=yeast.type,
            slug=yeast.id,
            chart_type='og',
            format=FORMAT_PNG,
        ))

    context = {'yeast': yeast, 'description': meta_provider.get_description_html(), 'meta': meta}

    return render(request, 'yeast/detail.html', context)


def chart(request: HttpRequest, slug: str, type_id: str, chart_type: str, format: str) -> HttpResponse:
    yeast = get_object_or_404(Yeast, pk=slug)

    if yeast.recipes_count <= 0:
        raise Http404("Yeast doesn't have any data.")

    if type_id != yeast.type:
        return redirect('yeast_chart', type_id=yeast.type, slug=yeast.id, chart_type=chart_type, format=format)

    if YeastChartFactory.is_supported_chart(chart_type):
        try:
            chart = YeastChartFactory.plot_chart(yeast, chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)


@cache_page(0)
def recipes(request: HttpRequest, slug: str, type_id: str) -> HttpResponse:
    yeast = get_object_or_404(Yeast, pk=slug)

    if yeast.recipes_count <= 0:
        raise Http404("Yeast doesn't have any data.")

    if type_id != yeast.type:
        return redirect('yeast_recipes', type_id=yeast.type, slug=yeast.id)

    recipes_list = YeastAnalysis(yeast).random_recipes(24)
    return render_recipes_list(recipes_list)


def group_by_type(yeasts: iter) -> list:
    yeast_types = {}
    types = Yeast.get_types()

    # Create type object
    for type in types:
        yeast_types[type] = {
            'id': type,
            'name': types[type],
            'yeasts': [],
            'most_popular': []
        }

    # Assign yeasts
    for yeast in yeasts:
        yeast_types[yeast.type]['yeasts'].append(yeast)

    # Filter types with yeasts
    types_filtered = []
    for yeast_type in yeast_types.values():
        if len(yeast_type['yeasts']):
            types_filtered.append(yeast_type)

    return types_filtered


def group_by_lab(yeasts: iter) -> Tuple[list, list]:
    other_yeasts = []
    labs = Yeast.get_labs()
    yeast_labs = {}

    # Create lab objects
    for lab in labs:
        yeast_labs[lab] = {
            'name': lab,
            'yeasts': [],
        }

    # Assign yeasts (if possible)
    for yeast in yeasts:
        yeast_labs[yeast.lab]['yeasts'].append(yeast)

    # Filter labs with yeasts
    labs_filtered = []
    for yeast_lab in yeast_labs.values():
        if len(yeast_lab['yeasts']) > 10:
            labs_filtered.append(yeast_lab)
        else:
            other_yeasts.extend(yeast_lab['yeasts'])

    return other_yeasts, labs_filtered
