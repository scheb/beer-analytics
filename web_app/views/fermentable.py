from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Fermentable
from web_app.charts.fermentable import FermentableChartFactory
from web_app.views.utils import render_plot


def overview(request: HttpRequest) -> HttpResponse:
    fermentable_categories = {}
    categories = Fermentable.get_categories()
    types = Fermentable.get_types()
    for category in categories:
        fermentable_types = {}
        for t in types:
            fermentable_types[t] = {
                'id': t,
                'name': types[t],
                'fermentables': [],
            }

        fermentable_categories[category] = {
            'id': category,
            'name': categories[category],
            'fermentables': [],
            'types': fermentable_types,
            'most_popular': []
        }

    fermentables = Fermentable.objects.filter().order_by('name')
    for fermentable in fermentables:
        if fermentable.type is not None:
            fermentable_categories[fermentable.category]['types'][fermentable.type]['fermentables'].append(fermentable)
        else:
            fermentable_categories[fermentable.category]['fermentables'].append(fermentable)

    fermentable_categories = fermentable_categories.values()
    for fermentable_category in fermentable_categories:
        types_filtered = []
        for t in fermentable_category['types'].values():
            if len(t['fermentables']) > 0:
                types_filtered.append(t)
        fermentable_category['types'] = types_filtered
        if len(fermentable_category['types']) > 1 or len(fermentable_category['fermentables']) > 5:
            fermentable_category['most_popular'] = Fermentable.objects.filter(category=fermentable_category['id']).order_by('-recipes_count')[:5]

    return render(request, 'fermentable/overview.html', {'categories': fermentable_categories})


def category(request: HttpRequest, category: str) -> HttpResponse:
    categories = Fermentable.get_categories()
    if category not in categories:
        raise Http404('Unknown fermentable category %s.' % category)

    fermentables_query = Fermentable.objects.filter(category=category, recipes_count__gt=0)

    fermentables = fermentables_query.order_by('name')
    if len(fermentables) > 5:
        most_popular = fermentables_query.order_by('-recipes_count')[:5]
    else:
        most_popular = []
    category_name = categories[category]

    return render(request, 'fermentable/category.html', {'category_name': category_name, 'fermentables': fermentables, 'most_popular': most_popular})


def detail(request: HttpRequest, slug: str, category: str) -> HttpResponse:
    fermentable = get_object_or_404(Fermentable, pk=slug)

    if fermentable.recipes_count <= 0:
        raise Http404("Fermentable doesn't have any data.")

    if category != fermentable.category:
        return redirect('fermentable_category', category=fermentable.category, slug=fermentable.id)

    return render(request, 'fermentable/detail.html', {'fermentable': fermentable})


def chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    fermentable = get_object_or_404(Fermentable, pk=id)

    chart_factory = FermentableChartFactory()
    if chart_factory.is_supported_chart(chart_type):
        plot = chart_factory.get_chart(fermentable, chart_type)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_plot(plot, format)
