from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Fermentable
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

    fermentables = Fermentable.objects.filter(recipes_count__gt=0).order_by('name')
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
        if len(fermentable_category['fermentables']) > 5:
            fermentable_category['most_popular'] = Fermentable.objects.filter(category=fermentable_category['id']).order_by('-recipes_count')[:5]

    return render(request, 'fermentable/overview.html', {'categories': fermentable_categories})


def category_detail(request: HttpRequest, *args, **kwargs):
    category = kwargs['category']

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


def detail(request: HttpRequest, *args, **kwargs):
    slug = kwargs['slug']
    category = kwargs['category']
    fermentable = get_object_or_404(Fermentable, pk=slug)

    if category != fermentable.category:
        return redirect('fermentable_category_detail', category=fermentable.category, slug=fermentable.id)

    return render(request, 'fermentable/detail.html', {'fermentable': fermentable})


def chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    fermentable = get_object_or_404(Fermentable, pk=id)

    raise Http404('Unknown chart type %s.' % chart_type)
    return render_plot(plot, format)
