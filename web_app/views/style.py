from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Style
from web_app.charts.style import StyleChartFactory
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart


def overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by('-recipes_count')
    most_popular = Style.objects.exclude(parent_style=None).order_by('-recipes_count')[:5]

    return render(request, 'style/overview.html', {'categories': categories, 'most_popular': most_popular})


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
    return render(request, 'style/detail.html', {"style": style})


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
