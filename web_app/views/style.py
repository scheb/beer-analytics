from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import cache_page

from recipe_db.analytics.spotlight.style import StyleAnalysis
from recipe_db.models import Style
from web_app.charts.style import StyleChartFactory
from web_app.charts.utils import NoDataException
from web_app.meta import StyleOverviewMeta, StyleMeta
from web_app.views.utils import render_chart, FORMAT_PNG, render_recipes_list


def overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by('-recipes_count')
    most_popular = Style.objects.exclude(parent_style=None).order_by('-recipes_count')[:5]

    meta = StyleOverviewMeta().get_meta()
    context = {'categories': categories, 'most_popular': most_popular, 'meta': meta}

    return render(request, 'style/overview.html', context)


def category(request: HttpRequest, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return display_style(request, style)


def detail(request: HttpRequest, slug: str, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category', category_slug=style.category.slug)
    if category_slug != style.category.slug:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return display_style(request, style)


def display_style(request: HttpRequest, style: Style) -> HttpResponse:
    meta = StyleMeta(style).get_meta()
    if style.recipes_count > 100:
        meta.image = reverse('style_chart', kwargs=dict(
            category_slug=style.category.slug,
            slug=style.slug,
            chart_type='og',
            format=FORMAT_PNG,
        ))

    context = {"style": style, 'meta': meta}
    return render(request, 'style/detail.html', context)


def category_chart(request: HttpRequest, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect('style_chart', category_slug=style.category.slug, slug=style.slug, chart_type=chart_type, format=format)

    return display_chart(request, style, chart_type, format)


def chart(request: HttpRequest, slug: str, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category_chart', category_slug=style.category.slug, chart_type=chart_type, format=format)
    if category_slug != style.category.slug:
        return redirect('style_chart', category_slug=style.category.slug, slug=style.slug, chart_type=chart_type, format=format)

    return display_chart(request, style, chart_type, format)


@cache_page(0)
def category_recipes(request: HttpRequest, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect('style_category_recipes', category_slug=style.category.slug)

    recipes_list = StyleAnalysis(style).random_recipes(24)
    return render_recipes_list(recipes_list)


@cache_page(0)
def recipes(request: HttpRequest, slug: str, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category_recipes', category_slug=style.category.slug)
    if category_slug != style.category.slug:
        return redirect('style_recipes', category_slug=style.category.slug, slug=style.slug)

    recipes_list = StyleAnalysis(style).random_recipes(24)
    return render_recipes_list(recipes_list)


def display_chart(request: HttpRequest, style: Style, chart_type: str, format: str) -> HttpResponse:
    filter_param = str(request.GET['filter']) if 'filter' in request.GET else None

    if StyleChartFactory.is_supported_chart(chart_type):
        try:
            chart = StyleChartFactory.plot_chart(style, chart_type, filter_param)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)
