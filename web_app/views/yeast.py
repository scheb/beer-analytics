from typing import Tuple

from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Yeast
from web_app.charts.utils import NoDataException
from web_app.charts.yeast import YeastChartFactory
from web_app.views.utils import render_chart


def overview(request: HttpRequest) -> HttpResponse:
    yeasts = Yeast.objects.filter(recipes_count__gt=0).order_by('name')
    yeast_types = group_by_type(yeasts)
    for yeast_type in yeast_types:
        if len(yeast_type['yeasts']) > 5:
            yeast_type['most_popular'] = Yeast.objects.filter(type=yeast_type['id']).order_by('-recipes_count')[:5]
        (yeast_type['yeasts'], yeast_type['brands']) = group_by_brand(yeast_type['yeasts'])

    return render(request, 'yeast/overview.html', {'types': yeast_types})


def type_overview(request: HttpRequest, type: str) -> HttpResponse:
    types = Yeast.get_types()
    if type not in types:
        raise Http404('Unknown yeast type %s.' % type)

    type_name = types[type]

    yeasts_query = Yeast.objects.filter(type=type, recipes_count__gt=0)
    (yeasts, brands) = group_by_brand(yeasts_query.order_by('name'))

    most_popular = []
    if yeasts_query.count() > 5:
        most_popular = yeasts_query.order_by('-recipes_count')[:5]

    return render(request, 'yeast/type.html', {
        'type_name': type_name,
        'yeasts': yeasts,
        'brands': brands,
        'most_popular': most_popular
    })


def detail(request: HttpRequest, slug: str, type: str) -> HttpResponse:
    yeast = get_object_or_404(Yeast, pk=slug)

    if yeast.recipes_count <= 0:
        raise Http404("Yeast doesn't have any data.")

    if type != yeast.type or slug != yeast.id:
        return redirect('yeast_detail', type=yeast.type, slug=yeast.id)

    return render(request, 'yeast/detail.html', {'yeast': yeast})


def chart(request: HttpRequest, slug: str, type: str, chart_brand: str, format: str) -> HttpResponse:
    yeast = get_object_or_404(Yeast, pk=slug)

    if yeast.recipes_count <= 0:
        raise Http404("Yeast doesn't have any data.")

    if type != yeast.type:
        return redirect('yeast_chart', type=yeast.type, slug=yeast.id, chart_brand=chart_brand, format=format)

    if YeastChartFactory.is_supported_chart(chart_brand):
        try:
            chart = YeastChartFactory.plot_chart(yeast, chart_brand)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart brand %s.' % chart_brand)

    return render_chart(chart, format)


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


def group_by_brand(yeasts: iter) -> Tuple[list, list]:
    other_yeasts = []
    brands = Yeast.get_brands()
    yeast_brands = {}

    # Create brand objects
    for brand in brands:
        yeast_brands[brand] = {
            'name': brand,
            'yeasts': [],
        }

    # Assign yeasts (if possible)
    for yeast in yeasts:
        yeast_brands[yeast.brand]['yeasts'].append(yeast)

    # Filter brands with yeasts
    brands_filtered = []
    for yeast_brand in yeast_brands.values():
        if len(yeast_brand['yeasts']) > 10:
            brands_filtered.append(yeast_brand)
        else:
            other_yeasts.extend(yeast_brand['yeasts'])

    return other_yeasts, brands_filtered
