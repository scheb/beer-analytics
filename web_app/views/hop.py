from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from recipe_db.models import Hop
from web_app.charts.hop import HopChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import HopMeta, HopOverviewMeta
from web_app.views.utils import render_chart, FORMAT_PNG


def overview(request: HttpRequest) -> HttpResponse:
    hop_categories = {}
    categories = Hop.get_categories()
    for category in categories:
        most_popular = Hop.objects.filter(use=category).order_by('-recipes_count')[:5]
        hop_categories[category] = {'id': category, 'name': categories[category], 'hops': [], 'most_popular': most_popular}

    hops = Hop.objects.filter(recipes_count__gt=0).order_by('name')
    for hop in hops:
        hop_categories[hop.use]['hops'].append(hop)

    meta = HopOverviewMeta().get_meta()
    context = {'categories': hop_categories.values(), 'meta': meta}

    return render(request, 'hop/overview.html', context)


def category(request: HttpRequest, category: str) -> HttpResponse:
    categories = Hop.get_categories()
    if category not in categories:
        raise Http404('Unknown hop category %s.' % category)

    hops_query = Hop.objects.filter(use=category, recipes_count__gt=0)

    hops = hops_query.order_by('name')
    most_popular = hops_query.order_by('-recipes_count')[:5]
    category_name = categories[category]

    meta = HopOverviewMeta(category_name).get_meta()
    context = {'category_name': category_name, 'hops': hops, 'most_popular': most_popular, 'meta': meta}

    return render(request, 'hop/category.html', context)


def detail(request: HttpRequest, slug: str, category: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug)

    if hop.recipes_count <= 0:
        raise Http404("Hop doesn't have any data.")

    if category != hop.category:
        return redirect('hop_detail', category=hop.category, slug=hop.id)

    meta_provider = HopMeta(hop)
    meta = meta_provider.get_meta()
    if hop.recipes_count > 100:
        meta.image = reverse('hop_chart', kwargs=dict(
            category=hop.category,
            slug=hop.id,
            chart_type='og',
            format=FORMAT_PNG,
        ))

    context = {'hop': hop, 'description': meta_provider.get_description_html(), 'meta': meta}

    return render(request, 'hop/detail.html', context)


def chart(request: HttpRequest, slug: str, category: str, chart_type: str, format: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=slug)

    if hop.recipes_count <= 0:
        raise Http404("Hop doesn't have any data.")

    if category != hop.category:
        return redirect('hop_chart', category=hop.category, slug=hop.id, chart_type=chart_type, format=format)

    if HopChartFactory.is_supported_chart(chart_type):
        try:
            chart = HopChartFactory.plot_chart(hop, chart_type)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)
