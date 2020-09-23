from django.http import HttpResponse, HttpRequest, Http404
from django.shortcuts import render, get_object_or_404, redirect

from recipe_db.models import Style
from web_app.charts.style import StyleChartFactory
from web_app.charts.utils import NoDataException
from web_app.views.utils import render_chart


def overview(request: HttpRequest) -> HttpResponse:
    categories = Style.objects.filter(parent_style=None).order_by('id')
    most_popular = Style.objects.exclude(parent_style=None).order_by('-recipes_count')[:5]

    return render(request, 'style/overview.html', {'categories': categories, 'most_popular': most_popular})


def category(request: HttpRequest, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=category_slug)

    if not style.is_category:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return render_style(request, style)


def detail(request: HttpRequest, slug: str, category_slug: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category', category_slug=style.category.slug)
    if category_slug != style.category.slug:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    return render_style(request, style)


def render_style(request: HttpRequest, style: Style) -> HttpResponse:
    return render(request, 'style/detail.html', {"style": style})


def chart(request: HttpRequest, slug: str, category_slug: str, chart_type: str, format: str) -> HttpResponse:
    style = get_object_or_404(Style, slug=slug)

    if style.is_category:
        return redirect('style_category', category_slug=style.category.slug)
    if category_slug != style.category.slug:
        return redirect('style_detail', category_slug=style.category.slug, slug=style.slug)

    filter_param = str(request.GET['filter']) if 'filter' in request.GET else None

    chart_factory = StyleChartFactory()
    if chart_factory.is_supported_chart(chart_type):
        try:
            chart = chart_factory.get_chart(style, chart_type, filter_param)
        except NoDataException:
            return HttpResponse(status=204)
    else:
        raise Http404('Unknown chart type %s.' % chart_type)

    return render_chart(chart, format)
