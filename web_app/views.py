from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.analytics import get_style_popularity, get_style_metric_values, get_style_popular_hops, \
    get_style_popular_fermentables, get_style_hop_pairings
from recipe_db.models import Style, Hop, Fermentable
from web_app.charts import LinesChart, CompactHistogramChart, BoxPlot, PairsBoxPlot


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


def legal(request: HttpRequest) -> HttpResponse:
    return render(request, 'legal.html')


def style_overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by('id')
    most_popular = Style.objects.exclude(parent_style=None).order_by('-recipes_count')[:5]

    return render(request, 'styles/overview.html', {'categories': categories, 'most_popular': most_popular})


def style_category_detail(request: HttpRequest, *args, **kwargs):
    category_slug = kwargs['category_slug']
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return render_style(request, style)


def style_detail(request: HttpRequest, *args, **kwargs):
    slug = kwargs['slug']
    category_slug = kwargs['category_slug']
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category_detail', category_slug=style.category.slug)
    if category_slug != style.category.slug:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return render_style(request, style)


def render_style(request: HttpRequest, style: Style) -> HttpResponse:
    return render(request, 'styles/detail.html', {
        "style": style
    })


def style_chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, pk=id)

    if chart_type == 'popularity':
        df = get_style_popularity(style)
        plot = LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes')
    elif chart_type == 'abv-histogram':
        df = get_style_metric_values(style, 'abv')
        plot = CompactHistogramChart().plot(df, 'abv', 'count')
    elif chart_type == 'ibu-histogram':
        df = get_style_metric_values(style, 'ibu')
        plot = CompactHistogramChart().plot(df, 'ibu', 'count')
    elif chart_type == 'color-histogram':
        df = get_style_metric_values(style, 'srm')
        plot = CompactHistogramChart().plot(df, 'srm', 'count')
    elif chart_type == 'original-plato-histogram':
        df = get_style_metric_values(style, 'og')
        plot = CompactHistogramChart().plot(df, 'og', 'count')
    elif chart_type == 'final-plato-histogram':
        df = get_style_metric_values(style, 'fg')
        plot = CompactHistogramChart().plot(df, 'fg', 'count')
    elif chart_type == 'popular-hops':
        df = get_style_popular_hops(style)
        plot = BoxPlot().plot(df, 'hop', 'amount_percent', 'Hops by Popularity', '% Amount')
    elif chart_type == 'popular-fermentables':
        df = get_style_popular_fermentables(style)
        plot = BoxPlot().plot(df, 'fermentable', 'amount_percent', 'Fermentables by Popularity', '% Amount')
    elif chart_type == 'hop-pairings':
        df = get_style_hop_pairings(style)
        plot = PairsBoxPlot().plot(df, 'pairing', 'hop', 'amount_percent', None, '% Amount')
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    if format == 'png':
        return HttpResponse(plot.render_png(), content_type='image/png')
    elif format == 'svg':
        return HttpResponse(plot.render_svg(), content_type='image/svg+xml')
    else:
        return HttpResponse(plot.render_json(), content_type='application/json')


def hop_overview(request: HttpRequest) -> HttpResponse:
    hop_categories = {}
    categories = Hop.get_categories()
    for category in categories:
        most_popular = Hop.objects.filter(use=category).order_by('-recipes_count')[:5]
        hop_categories[category] = {'id': category, 'name': categories[category], 'hops': [], 'most_popular': most_popular}

    hops = Hop.objects.filter(recipes_count__gt=0).order_by('name')
    for hop in hops:
        hop_categories[hop.use]['hops'].append(hop)

    return render(request, 'hops/overview.html', {'categories': hop_categories.values()})


def hop_category_detail(request: HttpRequest, *args, **kwargs):
    category = kwargs['category']

    categories = Hop.get_categories()
    if category not in categories:
        raise Http404('Unknown hop category %s.' % category)

    hops_query = Hop.objects.filter(use=category, recipes_count__gt=0)

    hops = hops_query.order_by('name')
    most_popular = hops_query.order_by('-recipes_count')[:5]
    category_name = categories[category]

    return render(request, 'hops/category.html', {'category_name': category_name, 'hops': hops, 'most_popular': most_popular})


def hop_detail(request: HttpRequest, *args, **kwargs):
    slug = kwargs['slug']
    category = kwargs['category']
    hop = get_object_or_404(Hop, pk=slug)

    if category != hop.category:
        return redirect('hop_category_detail', category=hop.category, slug=hop.id)

    return render(request, 'hops/detail.html', {'hop': hop})


def hop_chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    hop = get_object_or_404(Hop, pk=id)

    raise Http404('Unknown chart type %s.' % chart_type)

    if format == 'png':
        return HttpResponse(plot.render_png(), content_type='image/png')
    elif format == 'svg':
        return HttpResponse(plot.render_svg(), content_type='image/svg+xml')
    else:
        return HttpResponse(plot.render_json(), content_type='application/json')


def fermentable_overview(request: HttpRequest) -> HttpResponse:
    fermentable_categories = {}
    categories = Fermentable.get_categories()
    types = Fermentable.get_types()
    for category in categories:
        most_popular = Fermentable.objects.filter(category=category).order_by('-recipes_count')[:5]
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
            'most_popular': most_popular
        }

    fermentables = Fermentable.objects.filter(recipes_count__gt=0).order_by('name')
    for fermentable in fermentables:
        if fermentable.type is not None:
            fermentable_categories[fermentable.category]['types'][fermentable.type]['fermentables'].append(fermentable)
        else:
            fermentable_categories[fermentable.category]['fermentables'].append(fermentable)

    fermentable_categories = fermentable_categories.values()
    for fermentable in fermentable_categories:
        types_filtered = []
        for t in fermentable['types'].values():
            if len(t['fermentables']) > 0:
                types_filtered.append(t)
        fermentable['types'] = types_filtered

    return render(request, 'fermentables/overview.html', {'categories': fermentable_categories})


def fermentable_category_detail(request: HttpRequest, *args, **kwargs):
    category = kwargs['category']

    categories = Fermentable.get_categories()
    if category not in categories:
        raise Http404('Unknown fermentable category %s.' % category)

    fermentables_query = Fermentable.objects.filter(category=category, recipes_count__gt=0)

    fermentables = fermentables_query.order_by('name')
    most_popular = fermentables_query.order_by('-recipes_count')[:5]
    category_name = categories[category]

    return render(request, 'fermentables/category.html', {'category_name': category_name, 'fermentables': fermentables, 'most_popular': most_popular})


def fermentable_detail(request: HttpRequest, *args, **kwargs):
    slug = kwargs['slug']
    category = kwargs['category']
    fermentable = get_object_or_404(Fermentable, pk=slug)

    if category != fermentable.category:
        return redirect('fermentable_category_detail', category=fermentable.category, slug=fermentable.id)

    return render(request, 'fermentables/detail.html', {'fermentable': fermentable})


def fermentable_chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    fermentable = get_object_or_404(Fermentable, pk=id)

    raise Http404('Unknown chart type %s.' % chart_type)

    if format == 'png':
        return HttpResponse(plot.render_png(), content_type='image/png')
    elif format == 'svg':
        return HttpResponse(plot.render_svg(), content_type='image/svg+xml')
    else:
        return HttpResponse(plot.render_json(), content_type='application/json')


def yeast_overview(request):
    return render(request, 'yeasts/overview.html')
