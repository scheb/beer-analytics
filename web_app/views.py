from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Style, Hop, Fermentable, Recipe
from web_app.charts.style import StyleChartFactory
from web_app.plot import Plot

FORMAT_PNG = 'png'
FORMAT_SVG = 'svg'
FORMAT_JSON = 'json'
FORMATS = [FORMAT_PNG, FORMAT_SVG, FORMAT_JSON]


def render_plot(plot: Plot, data_format: str):
    if data_format == FORMAT_PNG:
        return HttpResponse(plot.render_png(), content_type='image/png')
    elif data_format == FORMAT_SVG:
        return HttpResponse(plot.render_svg(), content_type='image/svg+xml')
    elif data_format == FORMAT_JSON:
        return HttpResponse(plot.render_json(), content_type='application/json')
    else:
        raise Http404('Unknown plotting format %s.' % data_format)


def home(request: HttpRequest) -> HttpResponse:
    recipes = Recipe.objects.count()
    return render(request, 'index.html', {'recipes': recipes})


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
    return render(request, 'styles/detail.html', {"style": style})


def style_chart(request: HttpRequest, id: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, pk=id)

    chart_factory = StyleChartFactory()
    if chart_factory.is_supported_chart(chart_type):
        plot = chart_factory.get_chart(style, chart_type)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_plot(plot, format)


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
    return render_plot(plot, format)


def fermentable_overview(request: HttpRequest) -> HttpResponse:
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

    return render(request, 'fermentables/overview.html', {'categories': fermentable_categories})


def fermentable_category_detail(request: HttpRequest, *args, **kwargs):
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
    return render_plot(plot, format)


def yeast_overview(request):
    return render(request, 'yeasts/overview.html')
