from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Hop
from web_app.views.utils import render_plot


def overview(request: HttpRequest) -> HttpResponse:
    hop_categories = {}
    categories = Hop.get_categories()
    for category in categories:
        most_popular = Hop.objects.filter(use=category).order_by('-recipes_count')[:5]
        hop_categories[category] = {'id': category, 'name': categories[category], 'hops': [], 'most_popular': most_popular}

    hops = Hop.objects.filter(recipes_count__gt=0).order_by('name')
    for hop in hops:
        hop_categories[hop.use]['hops'].append(hop)

    return render(request, 'hop/overview.html', {'categories': hop_categories.values()})


def category_detail(request: HttpRequest, *args, **kwargs):
    category = kwargs['category']

    categories = Hop.get_categories()
    if category not in categories:
        raise Http404('Unknown hop category %s.' % category)

    hops_query = Hop.objects.filter(use=category, recipes_count__gt=0)

    hops = hops_query.order_by('name')
    most_popular = hops_query.order_by('-recipes_count')[:5]
    category_name = categories[category]

    return render(request, 'hop/category.html', {'category_name': category_name, 'hops': hops, 'most_popular': most_popular})


def detail(request: HttpRequest, *args, **kwargs):
    slug = kwargs['slug']
    category = kwargs['category']
    hop = get_object_or_404(Hop, pk=slug)

    if category != hop.category:
        return redirect('hop_category_detail', category=hop.category, slug=hop.id)

    return render(request, 'hop/detail.html', {'hop': hop})


def chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=id)

    raise Http404('Unknown chart type %s.' % chart_type)
    return render_plot(plot, format)
