from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.analytics import get_style_popularity, get_style_metric_values, get_style_popular_hops, \
    get_style_popular_fermentables, get_style_hop_pairings
from recipe_db.models import Style
from web_app.charts import LinesChart, CompactHistogramChart, BoxPlot, PairsBoxPlot


def home(request: HttpRequest) -> HttpResponse:
    return render(request, 'index.html')


def imprint(request: HttpRequest) -> HttpResponse:
    return render(request, 'imprint.html')


def privacy_policy(request: HttpRequest) -> HttpResponse:
    return render(request, 'privacy_policy.html')


def style_overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by('id')
    return render(request, 'styles/overview.html', {'categories': categories})


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
        id_to_name = style.get_id_name_mapping_including_sub_styles()
        df = get_style_popularity(style)
        plot = LinesChart().plot(df, 'month', 'recipes_percent', 'style', 'Month/Year', '% Recipes', category_names=id_to_name)
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
